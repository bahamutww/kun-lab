<div align="center">

<a href="https://kunpuai.com/"><img src="./frontend/src/assets/kunlab_bg_logo.svg" width="120" height="120" alt="kun-lab logo"></a>

# kun-lab

<p align="center">
  <a href="./README-EN.md">English</a> |
  <a href="./README.md">简体中文</a>
</p>

[![Version](https://img.shields.io/github/v/release/bahamutww/kun-lab?color=blue&include_prereleases&label=版本)](https://github.com/bahamutww/kun-lab/releases)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Windows Support](https://img.shields.io/badge/Windows-支持-blue.svg)](https://github.com/bahamutww/kun-lab/releases)

</div>

# kun-lab

**您的本地化智能对话伙伴**

kun-lab 是一款基于 Ollama 的轻量级 AI 对话应用，旨在为您提供简洁、高效、功能丰富的本地 AI 对话体验。无需繁琐的配置，开箱即用，即可轻松享受强大的 AI 能力，一切数据尽在本地掌控，保障您的隐私安全。

## 📑 目录

- [✨ 核心亮点](#-核心亮点)
- [📷 应用截图](#-应用截图)
- [🚀 快速上手](#-快速上手)
- [📚 使用指南](#-使用指南)
- [🔧 功能详解](#-功能详解)
- [🛠️ 技术栈](#️-技术栈)
- [📞 联系我们](#-联系我们)

## 📷 应用截图

<div align="center">
  <img src="./frontend/src/assets/home_page.jpg" width="80%" alt="首页界面">
  <p align="center"><em>首页界面 - 未收藏模型空状态</em></p>
</div>

<div align="center">
  <img src="./frontend/src/assets/homemodel_page.jpg" width="80%" alt="首页界面">
  <p align="center"><em>首页界面 - 收藏的模型在首页展示</em></p>
</div>

<div align="center">
  <img src="./frontend/src/assets/chat_page.jpg" width="80%" alt="聊天界面">
  <p align="center"><em>聊天界面 - 流畅的对话体验与丰富的功能支持</em></p>
</div>

<div align="center">
  <img src="./frontend/src/assets/model_page.jpg" width="80%" alt="模型管理界面">
  <p align="center"><em>模型管理 - 轻松管理和使用多种AI模型</em></p>
</div>

<div align="center">
  <img src="./frontend/src/assets/modeldetails_page.jpg" width="80%" alt="模型详情界面">
  <p align="center"><em>模型详情 - 本地模型的详细信息</em></p>
</div>

<div align="center">
  <img src="./frontend/src/assets/custom_page.jpg" width="80%" alt="自定义模型界面">
  <p align="center"><em>自定义模型 - 模型自定义让你获取更多控制扮演各种角色</em></p>
</div>


## ✨ 核心亮点
- **📱 桌面应用支持**：提供桌面应用，支持 Windows/macOS/Linux 平台（目前只支持Windows），开箱即用。
- **🚀 多模型灵活切换**：轻松管理和选用 Ollama 支持的各种模型，满足您不同的对话需求。
- **💬 极速流式对话**：体验如丝般顺畅的实时对话，AI 响应即时呈现。
- **📄 智能文档解析**：支持 PDF、DOC、PPT、TXT 等多种文档格式，快速理解文档内容，解答您的疑问。
- **🖼️ 多模态图片理解**：支持多模态模型，不仅能识别图像，更能理解图像背后的场景和意图，并支持基于图片的多轮对话。
- **🌐 联网搜索增强**：集成网络搜索能力，让 AI 拥有更广阔的知识面，可根据您的需求开启深度搜索应对更复杂的问题。
- **💻 代码渲染**：代码块自动渲染，支持多种编程语言，代码展示更清晰易懂。
- **🗂️ 模型库拓展**：支持huggingface和ollama开源模型拉取， GGUF、safetensors 模型格式，模型管理更自由。
- **📝 提示词模板**：内置丰富的提示词模板，并支持自定义和分类管理，轻松激发 AI 的创造力。
- **🔒 本地数据存储**：所有数据本地存储，注重用户隐私，安全可靠。
- **🌍 多语言支持**：支持中文、英文等多种语言界面，满足不同用户的使用需求。
- **👥 多用户并发支持**：支持多用户独立登录和同时在线，每位用户拥有独立的对话空间和个性化设置，满足家庭、小团队或组织内多人共享使用的场景，提高资源利用效率。
- **✍️ 快速笔记功能**：支持 Markdown 语法，提供实时预览，支持一键导出，让知识整理更高效。

## 🚀 快速上手

### 桌面应用安装（推荐）

1. **下载安装包**：
   - 访问 [Release 页面](https://github.com/bahamutww/kun-lab/releases) 下载对应平台的安装包
   - Windows: `.exe` 安装程序（目前只支持Windows）
   - macOS: `.dmg` 安装包
   - Linux: `.AppImage` 或 `.deb` 包

2. **安装运行**：
   - 双击安装包，按照提示完成安装
   - 安装完成后即可直接运行，无需配置环境

## 📚 使用指南

#### 环境要求

- **操作系统**：Windows/macOS/Linux（Windows 推荐）
- **Python**：3.10+
- **Node.js**：20.16.0+
- **Ollama 服务**：确保 Ollama 服务已正确安装并运行

#### 安装步骤

1. **获取代码**：

   ```bash
   git clone https://github.com/bahamutww/kun-lab.git
   cd kun-lab
   ```

2. **虚拟环境安装**：

   ```bash
   python -m venv venv
   .\venv\Scripts\activate  # Windows
   # source venv/bin/activate  # macOS/Linux
   ```

3. **配置后端环境**：

   ```bash
   cd backend
   python setup.py or pip install -r requirements.txt
   ```

4. **配置前端环境**：

   ```bash
   cd frontend
   npm install
   ```

5. **环境变量配置**：

   ```bash
   # 复制 .env.example 为 .env
   cp .env.example .env
   # 根据您的实际情况修改 .env 文件中的配置项
   ```

6. **启动 kun-lab**：

   ```bash
   # 在项目根目录下运行（后端依赖安装后启动该脚本）
   python run_dev.py
   ```

7. 打开浏览器，访问 http://localhost:5173 即可开始体验 kun-lab！


## 🔧 功能详解

### 🤖 智能 AI 对话

- **多轮互动**：自然流畅的多轮对话体验，深入交流，探索更多。
- **实时流式响应**：告别漫长等待，AI 响应实时呈现，对话更高效。
- **历史记录管理**：方便的历史记录查看和管理，随时回顾精彩对话。
- **网络搜索**：集成网络搜索功能，AI 能够访问互联网信息，提供更全面、更及时的答案。
- **代码渲染**：智能识别并渲染代码块，提升代码阅读体验。

### 📄 智能文档对话

- **多格式文档支持**：支持 PDF、DOC、PPT、TXT 等多种文档格式上传解析。
- **深入文档理解**：AI 能够理解文档内容和结构，进行深层次的对话互动。
- **上下文关联**：基于文档内容进行上下文相关的对话，解答您的特定问题。
- **文档内容检索**：快速检索文档内的关键信息，提升信息获取效率。

### 🖼️ 多模态图片识别

- **多格式图片**：支持 JPG、PNG、JPEG 等常见图片格式。
- **智能场景识别**：运用多模态模型，精准识别图片场景和物体。
- **OCR 文字提取**：强大的 OCR 功能，快速提取图片中的文字信息。
- **基于图片的多轮对话**：就图片内容进行多轮深入对话，探索图像背后的故事。

### 📝 灵活提示词管理

- **内置提示词模板**：精选常用提示词模板，快速上手，激发灵感。
- **自定义提示词**：自由创建和编辑提示词，满足您的个性化需求。
- **分类管理**：对提示词进行分类管理，方便查找和使用。
- **一键应用**：快速应用提示词，简化操作流程。

### 🗂️ 强大的模型库

- **多模型管理**：集中管理您在 Ollama 中安装的各种模型。
- **模型信息展示**：清晰展示模型名称、大小等信息。
- **模型快速切换**：一键切换当前使用的模型，体验不同模型的特性。
- **模型库拓展**：支持huggingface、ollama的GGUF、safetensors模型拉取、扩充您的模型库。

### 🌍 多语言支持

- **界面语言切换**：支持中文、英文等多种语言界面，满足不同用户的使用需求。
- **语言设置持久化**：语言偏好会被保存，下次访问时自动应用。
- **全局翻译**：应用内所有文本元素均支持多语言显示，包括按钮、提示、标签等。

### ✍️ 快速笔记功能

- **Markdown 支持**：支持完整的 Markdown 语法，包括标题、列表、代码块、表格等。
- **实时预览**：编辑时实时预览渲染效果，所见即所得。
- **一键导出**：支持导出为 MD 格式，方便分享和存档。

## 🔮 未来规划 (Roadmap)

- **Agent 功能**：实现更智能的 Agent 系统，处理复杂任务。
- **工具调用功能**：支持调用外部工具和服务，扩展 AI 能力。
- **语音对话功能**：添加语音识别和合成，实现语音交互。

## 🛠️ 技术栈

### 后端

- **FastAPI**：构建高性能 API 服务
- **WebSocket**：实现实时双向通信
- **JWT 认证**：保障 API 安全
- **PDF 处理**：强大的 PDF 文档解析能力
- **OCR 引擎**：高效的文字识别引擎

### 前端

- **Vue 3**：构建交互式用户界面
- **TypeScript**：增强代码可维护性
- **WebSocket**：支持实时通信
- **国际化框架**：提供多语言支持

## 📂 目录结构

```
kun-lab/
├── backend/             # 后端代码
│   ├── api/             # API 接口
│   ├── core/            # 核心功能模块
│   └── data/            # 数据存储相关
├── frontend/            # 前端代码
│   ├── src/             # 源代码
│   │   ├── i18n/        # 国际化相关
│   │   ├── api/         # API 客户端
│   │   └── components/  # UI 组件
│   └── public/          # 静态资源
└── run_dev.py           # 开发服务器启动脚本
```

## 🧑‍💻 开发指南

### 开发模式启动

```bash
# 启动完整开发服务器（前端 + 后端）
python run_dev.py

# 仅启动后端服务
cd backend
python main.py

# 仅启动前端服务
cd frontend
npm run dev
```

## kun-lab 操作指南

## 1. 拉取模型

### 步骤：
1. 进入"模型库"页面
2. 点击"拉取模型"按钮
3. 在输入框中输入 `ollama run + 模型名称`，然后确认开始拉取

### 提示：
- 可在 [Ollama 官方模型列表](https://ollama.com/library) 查看模型名称，例如：`ollama run qwq:32b`
- 也支持 Hugging Face 上 GGUF 格式模型，输入格式为 `ollama run hf.co/账号/模型名称`，例如：`ollama run hf.co/Qwen/QwQ-32B-GGUF:Q2_K`

## 2. 聊天对话

### 步骤：
1. 进入"聊天对话"页面
2. 通过以下任一方式开始：
   - 点击侧边导航栏的"新对话"
   - 在首页点击"开始新对话"按钮
   - 选择指定模型后点击"开始新对话"
3. 开始与您的模型愉快聊天！

## 3. 自定义模型（Modelfile）

### 步骤：
1. 进入"模型库"页面
2. 点击"自定义"按钮
3. 输入模型名称（支持中文）
4. 选择基础模型
5. 输入系统提示词（用于定义角色或行为）
6. 点击创建，完成自定义

### 提示：
- 如果提示词定义了一个角色，新模型将以该角色身份与您对话


## 🤝 参与贡献

我们非常欢迎您为 kun-lab 项目贡献力量！

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/your-feature`)
3. 提交您的代码更改 (`git commit -am 'Add some feature'`)
4. 推送分支 (`git push origin feature/your-feature`)
5. 发起 Pull Request

## 📜 许可证

Apache 2.0 License

## 🔗 更多资源

- 项目文档: `docs/`
- 更新日志: `CHANGELOG.md`
- 问题反馈: `issues`

## 🙏 特别感谢

- [Ollama](https://ollama.ai/)：强大的本地模型运行框架
- [FastAPI](https://fastapi.tiangolo.com/)：现代化的 Web API 框架
- [Vue](https://vuejs.org/)：流行的 JavaScript UI 库

## 📞 联系我们

如果您有任何问题或建议，欢迎通过以下方式与我们联系：

- 提交 Issue：在 GitHub 仓库 issues 页面提交您的问题或建议。

- 邮件：发送至 [service@kunpuai.com](service@kunpuai.com)

> 温馨提示：kun-lab 仍在快速迭代开发中，您的贡献和反馈对我们至关重要！
