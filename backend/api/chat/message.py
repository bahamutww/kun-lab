from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, AsyncGenerator, List, Optional
from datetime import datetime
import sys
from pathlib import Path
import websockets.exceptions
import json
import logging
import asyncio
from ollama.types import ChatRequest, ChatMessage
from database import Database, get_db
from api.auth import get_current_user, decode_token
from config import API_CONFIG
from ollama.client import OllamaClient
from .schemas import ChatCompletionRequest
from api.tools.doc_format import get_mime_type_from_filename

router = APIRouter()

# 客户端池配置
CLIENT_POOL_SIZE = 3  # 可以根据服务器性能调整

# 客户端池和信号量
ollama_clients = []
client_semaphores = []

# 初始化客户端池
for _ in range(CLIENT_POOL_SIZE):
    ollama_clients.append(OllamaClient(API_CONFIG["OLLAMA_BASE_URL"]))
    client_semaphores.append(asyncio.Semaphore(1))

# 用于存储活跃的 WebSocket 连接
active_connections: Dict[str, WebSocket] = {}

# 全局请求队列锁
request_queue_lock = asyncio.Lock()

async def get_available_client() -> tuple[OllamaClient, int, asyncio.Semaphore]:
    """获取一个可用的客户端实例和对应的信号量"""
    # 使用全局锁来确保客户端分配的原子性
    async with request_queue_lock:
        # 查找最先可用的客户端
        for i, semaphore in enumerate(client_semaphores):
            if semaphore.locked():
                continue
            
            # 返回客户端、索引和信号量
            return ollama_clients[i], i, semaphore
        
        # 如果所有客户端都在使用中，使用轮询策略选择一个
        # 这确保了请求不会被无限期阻塞
        client_index = 0  # 默认使用第一个客户端
        return ollama_clients[client_index], client_index, client_semaphores[client_index]

async def process_chat_messages(
    messages: List[Dict[str, Any]],
    model: str,
    web_search: bool = False,
    username: str = None
) -> AsyncGenerator[str, None]:
    """处理聊天消息并生成响应流"""
    # 获取可用的客户端实例
    client, client_index, semaphore = await get_available_client()
    
    # 使用信号量控制对客户端的访问
    async with semaphore:
        try:
            logging.info(f"开始处理聊天消息，使用模型: {model}, 网页搜索: {web_search}, 客户端索引: {client_index}")
            # 转换消息格式，确保图片数据正确传递
            formatted_messages = []
            for msg in messages:
                formatted_msg = {
                    "role": msg["role"],
                    "content": msg["content"]
                }
                # 如果有图片数据，添加到消息中
                if "image" in msg and msg["image"]:
                    formatted_msg["images"] = [msg["image"]]  # Ollama API 需要 images 数组
                
                # 如果有文档数据，将文档内容添加到消息中
                if "document" in msg and msg["document"]:
                    # 文档内容是 Markdown 文本
                    doc_content = msg["document"]
                    
                    # 提取文件名（如果有）
                    file_name = "文档"
                    import re
                    match = re.search(r"# 文件: (.+?)\n", doc_content)
                    if match:
                        file_name = match.group(1)
                    
                    # 如果文档内容太长，可能需要截断
                    max_doc_length = 200000  # 设置一个合理的最大长度
                    if len(doc_content) > max_doc_length:
                        doc_content = doc_content[:max_doc_length] + "...\n[文档内容过长，已截断]"
                    
                    # 添加文档内容到消息中
                    formatted_msg["content"] = formatted_msg["content"] + f"\n\n以下是《{file_name}》的内容：\n" + doc_content
                    
                    # 打印调试信息
                    logging.debug(f"添加文档内容到消息中，文档名称: {file_name}，文档长度: {len(doc_content)}")
                
                formatted_messages.append(formatted_msg)

            # 如果启用了网页搜索，调用 Tavily 搜索工具
            if web_search and messages[-1]["role"] == "user":
                from api.tools.tavily_search import search_web
                try:
                    search_query = messages[-1]["content"]
                    search_results = await search_web(search_query, username=username)
                    
                    # 检查搜索结果
                    if search_results and "results" in search_results and search_results["results"]:
                        # 将搜索结果添加到系统消息中
                        search_content = "\n\n网页搜索结果:\n"
                        for idx, result in enumerate(search_results["results"], 1):
                            search_content += f"{idx}. {result['title']}: {result['url']}\n{result['content']}\n\n"
                        
                        # 添加系统消息，提供搜索结果
                        formatted_messages.insert(0, {
                            "role": "system",
                            "content": f"以下是与用户问题相关的网页搜索结果，请在回答时参考这些信息：{search_content}"
                        })
                        logging.info(f"已添加网页搜索结果到消息中")
                    elif search_results and "error" in search_results:
                        # 如果有错误，添加错误信息到系统消息
                        error_message = search_results["error"]
                        formatted_messages.insert(0, {
                            "role": "system",
                            "content": f"用户启用了网页搜索功能，但搜索失败: {error_message}。请在回答中告知用户搜索功能当前不可用，建议检查Tavily API密钥配置。"
                        })
                        logging.warning(f"网页搜索失败: {error_message}")
                    else:
                        # 如果没有结果，添加提示信息
                        formatted_messages.insert(0, {
                            "role": "system",
                            "content": "用户启用了网页搜索功能，但未找到相关搜索结果。请基于您已有的知识回答问题。"
                        })
                        logging.info("网页搜索未返回结果")
                except Exception as e:
                    # 捕获搜索过程中的异常
                    error_message = str(e)
                    formatted_messages.insert(0, {
                        "role": "system",
                        "content": f"用户启用了网页搜索功能，但搜索过程中发生错误: {error_message}。请在回答中告知用户搜索功能当前不可用。"
                    })
                    logging.error(f"网页搜索异常: {error_message}")
            
            chat_request = ChatRequest(
                model=model,
                messages=[ChatMessage(**msg) for msg in formatted_messages],
                stream=True
            )
            
            # 使用分配的客户端处理请求
            async for chunk in client.chat(chat_request):
                yield json.dumps({
                    "model": model,
                    "message": {
                        "role": "assistant",
                        "content": chunk.message.content if chunk.message else ""
                    },
                    "done": chunk.done
                })
                
            logging.info(f"完成处理聊天消息，客户端索引: {client_index}")
        except Exception as e:
            error_msg = f"处理消息时出错: {str(e)}"
            logging.error(f"客户端 {client_index} 处理消息时出错: {error_msg}")
            logging.exception(e)  # 记录完整的错误堆栈
            yield json.dumps({
                "error": error_msg,
                "model": model,
                "message": {
                    "role": "assistant",
                    "content": f"抱歉，处理消息时出现错误：{str(e)}"
                }
            })

def get_limited_history(messages, max_messages=20):
    """限制历史消息数量，保留最近的消息"""
    if len(messages) <= max_messages:
        return messages
    
    # 保留最后 max_messages 条消息
    limited_messages = messages[-max_messages:]
    
    # 确保每条消息都有正确的格式
    for msg in limited_messages:
        # 确保文档字段格式正确
        if "document" in msg and msg["document"]:
            # 文档内容是 Markdown 文本
            document_content = msg["document"]
            
            # 尝试从文档内容中提取文件名
            file_name = "document.md"
            file_type = get_mime_type_from_filename(file_name)
            
            # 从 Markdown 内容中提取文件名
            import re
            match = re.search(r"# 文件: (.+?)\n", document_content)
            if match:
                file_name = match.group(1)
                file_type = get_mime_type_from_filename(file_name)
            
            # 构建文档对象，用于前端显示
            msg["document"] = {
                "name": file_name,
                "content": document_content,
                "type": file_type
            }
    
    return limited_messages

async def save_message(
    db: Database,
    conversation_id: str,
    role: str,
    content: str,
    images: str = None,
    document: str = None
):
    """保存消息到数据库
    
    Args:
        db: 数据库连接
        conversation_id: 对话ID
        role: 消息角色
        content: 消息内容
        images: 图片数据，JSON数组格式存储图片路径
        document: 文档数据，Markdown 格式
    """
    timestamp = datetime.utcnow().isoformat()
    
    # 记录调试信息
    if images:
        logging.debug(f"Saving message with image data for conversation {conversation_id}")
        # 确保 images 是字符串类型
        if not isinstance(images, str):
            images = json.dumps(images) if images is not None else None
            
    if document:
        logging.debug(f"Saving message with document data for conversation {conversation_id}")
        # 确保 document 是字符串类型
        if not isinstance(document, str):
            try:
                document = json.dumps(document) if document is not None else None
            except:
                document = str(document) if document is not None else None
    
    # 打印参数类型，用于调试
    logging.debug(f"Parameter types: conversation_id={type(conversation_id)}, role={type(role)}, "
                  f"content={type(content)}, images={type(images)}, document={type(document)}, "
                  f"timestamp={type(timestamp)}")
    
    await db.execute(
        """
        INSERT INTO messages (conversation_id, role, content, images, document, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (conversation_id, role, content, images, document, timestamp)
    )
    
    # 更新对话的更新时间
    await db.execute(
        """
        UPDATE conversations
        SET updated_at = ?
        WHERE id = ?
        """,
        (timestamp, conversation_id)
    )
    await db.commit()

async def get_conversation_messages(
    db: Database,
    conversation_id: str,
    current_user: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """获取对话的所有消息"""
    # 验证对话所有权
    conversation = await db.fetch_one(
        """
        SELECT id FROM conversations
        WHERE id = ? AND user_id = ?
        """,
        (conversation_id, current_user["username"])
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="对话不存在")
    
    # 获取消息历史
    messages = await db.fetch_all(
        """
        SELECT role, content, created_at
        FROM messages
        WHERE conversation_id = ?
        ORDER BY created_at ASC
        """,
        (conversation_id,)
    )
    return messages

@router.post("/conversations/{conversation_id}/abort")
async def abort_generation(
    conversation_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    """中止指定对话的生成过程"""
    try:
        # 确保数据库连接有效
        await db.ensure_connected()
        
        # 检查对话是否存在且属于当前用户
        conversation = await db.fetch_one(
            """
            SELECT id FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, current_user["username"])
        )
        
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在或您无权访问")
            
        # 检查用户是否有权限操作该对话
        if conversation_id not in active_connections:
            return {"status": "success", "message": "没有找到活跃的生成过程"}
            
        # 关闭 WebSocket 连接
        ws = active_connections[conversation_id]
        if ws and not ws.client_state.disconnected:
            await ws.close(code=1000, reason="用户请求停止生成")
            active_connections.pop(conversation_id, None)
            logging.info(f"已停止对话 {conversation_id} 的生成过程")
            
        return {"status": "success", "message": "已停止生成"}
    except Exception as e:
        error_msg = f"停止生成时出错: {str(e)}"
        logging.error(error_msg)
        logging.exception(e)
        raise HTTPException(status_code=500, detail=error_msg)

@router.websocket("/conversations/{conversation_id}/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str,
    db: Database = Depends(get_db)
):
    await websocket.accept()
    
    try:
        # 验证token
        if not token:
            await websocket.close(code=4001, reason="未提供认证token")
            return
        
        try:
            payload = decode_token(token)
            username = payload.get("sub")
            if not username:
                await websocket.close(code=4001, reason="无效的token")
                return
        except:
            await websocket.close(code=4001, reason="无效的token")
            return
        
        # 验证对话所有权
        conversation = await db.fetch_one(
            """
            SELECT model FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, username)
        )
        if not conversation:
            await websocket.close(code=4004, reason="对话不存在")
            return
            
        # 将连接添加到活跃连接列表
        active_connections[conversation_id] = websocket
        
        while True:
            try:
                # 接收消息
                data = await websocket.receive_json()
                
                if data.get("type") != "chat":
                    continue
                
                # 获取历史消息
                history_messages = await db.fetch_all(
                    """
                    SELECT role, content, images, document
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY created_at ASC
                    """,
                    (conversation_id,)
                )
                
                # 构建完整的消息列表
                all_messages = []
                
                # 获取用户偏好设置
                user_prefs = await db.fetch_one(
                    "SELECT preferences FROM users WHERE username = ?",
                    (username,)
                )
                user_preferences = json.loads(user_prefs["preferences"] or "{}")
                
                # 添加历史消息，先收集系统消息
                system_messages = []
                other_messages = []
                
                for msg in history_messages:
                    message_dict = {
                        "role": msg["role"],
                        "content": msg["content"]
                    }
                    if msg["images"]:
                        message_dict["image"] = msg["images"]
                    if msg["document"]:
                        message_dict["document"] = msg["document"]
                    
                    if msg["role"] == "system":
                        system_messages.append(message_dict)
                    else:
                        other_messages.append(message_dict)
                
                # 如果用户偏好中启用了个人信息，添加到系统消息中
                if user_preferences.get("use_personal_info", False) and user_preferences.get("personal_info"):
                    personal_info = user_preferences.get("personal_info", "").strip()
                    
                    # 获取用户昵称
                    nickname = user_preferences.get("nickname")
                    
                    if personal_info:
                        # 如果有昵称且个人信息中没有包含昵称信息，则添加昵称
                        if nickname and nickname.strip() and not any(keyword in personal_info.lower() for keyword in [f"我叫{nickname}", f"我的名字是{nickname}", f"我是{nickname}"]):
                            personal_info = f"我的名字是{nickname}。{personal_info}"
                        
                        system_message = {
                            "role": "system",
                            "content": f"用户的个人信息：{personal_info}"
                        }
                        system_messages.append(system_message)
                        logging.info("已添加用户个人偏好信息到系统消息")
                
                # 合并所有消息
                all_messages = system_messages + other_messages
                # 添加当前用户消息
                current_message = data.get("messages", [])[-1]
                if current_message["role"] == "user":
                    # 获取文档数据
                    document_data = current_message.get("document")
                    
                    # 确保 document_data 是字符串类型
                    if document_data and not isinstance(document_data, str):
                        try:
                            # 如果是字典类型，尝试将其转换为 Markdown 格式
                            if isinstance(document_data, dict):
                                if "content" in document_data:
                                    document_content = document_data["content"]
                                    # 如果有文件名，添加到内容开头（仅当内容中不包含文件名时）
                                    if "name" in document_data and not document_content.startswith(f"# 文件: {document_data['name']}"):
                                        file_name = document_data["name"]
                                        document_content = f"# 文件: {file_name}\n\n{document_content}"
                                    document_data = document_content
                                else:
                                    # 如果没有 content 字段，转换为字符串
                                    document_data = json.dumps(document_data)
                            else:
                                # 其他类型转换为字符串
                                document_data = str(document_data)
                        except Exception as e:
                            logging.error(f"处理文档数据时出错: {str(e)}")
                            document_data = str(document_data) if document_data is not None else None
                    
                    # 获取图片数据
                    image_data = current_message.get("image")
                    # 确保 image_data 是字符串类型
                    if image_data and not isinstance(image_data, str):
                        try:
                            image_data = json.dumps(image_data)
                        except:
                            image_data = str(image_data)
                    
                    await save_message(
                        db,
                        conversation_id,
                        current_message["role"],
                        current_message["content"],
                        image_data,
                        document_data
                    )
                    all_messages.append({
                        "role": current_message["role"],
                        "content": current_message["content"],
                        "image": image_data,
                        "document": document_data
                    })
                
                # 限制发送给模型的历史消息数量
                limited_messages = get_limited_history(all_messages)
                
                # 使用完整的消息历史进行对话
                model = data.get("model") or conversation["model"] or API_CONFIG["DEFAULT_MODEL"]
                
                # 获取网页搜索标志
                web_search_enabled = data.get("web_search", False)
                
                # 收集完整的AI回复
                full_response = ""
                try:
                    async for chunk in process_chat_messages(limited_messages, model, web_search_enabled, username=username):
                        await websocket.send_text(chunk)
                        # 解析响应以获取内容
                        chunk_data = json.loads(chunk)
                        if "message" in chunk_data:
                            full_response += chunk_data["message"]["content"]
                        # 如果是最后一条消息，保存到数据库
                        if chunk_data.get("done", False) and full_response:
                            await save_message(
                                db,
                                conversation_id,
                                "assistant",
                                full_response,
                                None,  # AI 回复没有图片
                                None   # AI 回复没有文档
                            )
                except websockets.exceptions.ConnectionClosedOK:
                    # 用户主动关闭连接，记录信息日志
                    logging.info(f"用户主动关闭了WebSocket连接 (conversation_id: {conversation_id})")
                    if full_response:
                        # 保存已生成的回复
                        await save_message(
                            db,
                            conversation_id,
                            "assistant",
                            full_response,
                            None,  # AI 回复没有图片
                            None   # AI 回复没有文档
                        )
                    break
                
            except WebSocketDisconnect:
                logging.info(f"WebSocket连接断开 (conversation_id: {conversation_id})")
                break
            except Exception as e:
                if isinstance(e, websockets.exceptions.ConnectionClosedOK):
                    logging.info(f"用户主动关闭了WebSocket连接 (conversation_id: {conversation_id})")
                else:
                    error_msg = f"处理WebSocket消息时出错: {str(e)}"
                    logging.error(error_msg)
                    logging.exception(e)
                    try:
                        await websocket.send_json({
                            "error": error_msg
                        })
                    except:
                        pass
                break
    
    except WebSocketDisconnect:
        logging.info(f"WebSocket连接断开 (conversation_id: {conversation_id})")
    except Exception as e:
        if isinstance(e, websockets.exceptions.ConnectionClosedOK):
            logging.info(f"用户主动关闭了WebSocket连接 (conversation_id: {conversation_id})")
        else:
            logging.error(f"WebSocket错误: {str(e)}")
            logging.exception(e)
    finally:
        # 确保连接从活跃列表中移除
        active_connections.pop(conversation_id, None)

@router.post("/conversations/{conversation_id}/chat")
async def chat(
    conversation_id: str,
    request: ChatCompletionRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Database = Depends(get_db)
):
    try:
        # 验证对话所有权
        conversation = await db.fetch_one(
            """
            SELECT model FROM conversations
            WHERE id = ? AND user_id = ?
            """,
            (conversation_id, current_user["username"])
        )
        if not conversation:
            raise HTTPException(status_code=404, detail="对话不存在")
        
        # 获取模型名称
        model = request.model or conversation["model"] or API_CONFIG["DEFAULT_MODEL"]
        logging.info(f"使用模型 {model} 处理对话 {conversation_id}")
        
        # 获取用户偏好设置
        user_prefs = await db.fetch_one(
            "SELECT preferences FROM users WHERE username = ?",
            (current_user["username"],)
        )
        user_preferences = json.loads(user_prefs["preferences"] or "{}")
        
        # 获取历史消息
        history_messages = await db.fetch_all(
            """
            SELECT role, content, images, document
            FROM messages
            WHERE conversation_id = ?
            ORDER BY created_at ASC
            """,
            (conversation_id,)
        )
        
        # 构建完整的消息列表，包含历史消息
        all_messages = []
        
        # 分离系统消息和其他消息
        system_messages = []
        other_messages = []
        
        # 添加历史消息
        for msg in history_messages:
            message_dict = {
                "role": msg["role"],
                "content": msg["content"]
            }
            if msg["images"]:
                message_dict["image"] = msg["images"]
            if msg["document"]:
                message_dict["document"] = msg["document"]
            
            if msg["role"] == "system":
                system_messages.append(message_dict)
            else:
                other_messages.append(message_dict)
        
        # 如果用户偏好中启用了个人信息，添加系统消息
        if user_preferences.get("use_personal_info", True) and user_preferences.get("personal_info"):
            personal_info = user_preferences.get("personal_info", "").strip()
            
            # 获取用户昵称
            nickname = user_preferences.get("nickname")
            
            if personal_info:
                # 如果有昵称且个人信息中没有包含昵称信息，则添加昵称
                if nickname and nickname.strip() and not any(keyword in personal_info.lower() for keyword in [f"我叫{nickname}", f"我的名字是{nickname}", f"我是{nickname}"]):
                    personal_info = f"我的名字是{nickname}。{personal_info}"
                
                system_message = {
                    "role": "system",
                    "content": f"用户的个人信息：{personal_info}"
                }
                system_messages.append(system_message)
                logging.info("已添加用户个人偏好信息到系统消息")
        
        # 合并所有消息
        all_messages = system_messages + other_messages
        
        # 添加当前用户消息
        if request.messages and request.messages[-1].role == "user":
            message = request.messages[-1]
            # 获取文档数据
            document_data = None
            if hasattr(message, "document"):
                document_data = message.document
                # 如果 document_data 是 Document 对象，将其转换为字典
                if hasattr(document_data, "model_dump"):
                    document_data = document_data.model_dump()
                
                # 确保 document_data 是字符串类型
                if document_data and not isinstance(document_data, str):
                    try:
                        # 如果是字典类型，尝试将其转换为 Markdown 格式
                        if isinstance(document_data, dict):
                            if "content" in document_data:
                                document_content = document_data["content"]
                                # 如果有文件名，添加到内容开头（仅当内容中不包含文件名时）
                                if "name" in document_data and not document_content.startswith(f"# 文件: {document_data['name']}"):
                                    file_name = document_data["name"]
                                    document_content = f"# 文件: {file_name}\n\n{document_content}"
                                document_data = document_content
                            else:
                                # 如果没有 content 字段，转换为字符串
                                document_data = json.dumps(document_data)
                        else:
                            # 其他类型转换为字符串
                            document_data = str(document_data)
                    except Exception as e:
                        logging.error(f"处理文档数据时出错: {str(e)}")
                        document_data = str(document_data) if document_data is not None else None
            
            # 获取图片数据
            image_data = message.image if hasattr(message, "image") else None
            # 确保 image_data 是字符串类型
            if image_data and not isinstance(image_data, str):
                try:
                    image_data = json.dumps(image_data)
                except:
                    image_data = str(image_data)
            
            await save_message(
                db,
                conversation_id,
                "user",
                message.content,
                image_data,
                document_data
            )
            all_messages.append({
                "role": message.role,
                "content": message.content,
                "image": image_data,
                "document": document_data  # 直接传递完整的文档数据
            })
        
        # 限制发送给模型的历史消息数量
        limited_messages = get_limited_history(all_messages)
        
        if request.stream:
            # 流式响应
            return StreamingResponse(
                process_chat_messages(limited_messages, model, request.web_search, username=current_user["username"]),
                media_type="text/event-stream"
            )
        else:
            # 完整响应
            full_response = ""
            error_occurred = False
            async for chunk in process_chat_messages(limited_messages, model, request.web_search, username=current_user["username"]):
                chunk_data = json.loads(chunk)
                if "error" in chunk_data:
                    error_occurred = True
                    raise HTTPException(
                        status_code=500,
                        detail=chunk_data["error"]
                    )
                if "message" in chunk_data:
                    full_response += chunk_data["message"]["content"]
            
            if not error_occurred and full_response:
                # 保存助手回复
                await save_message(
                    db,
                    conversation_id,
                    "assistant",
                    full_response,
                    None,  # AI 回复没有图片
                    None   # AI 回复没有文档
                )
            
            return {
                "model": model,
                "message": {
                    "role": "assistant",
                    "content": full_response
                }
            }
    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"处理对话请求时出错: {str(e)}"
        logging.error(error_msg)
        logging.exception(e)
        raise HTTPException(status_code=500, detail=error_msg)
