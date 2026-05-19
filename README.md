# Cyan_Edition

## 目录

- [1. 项目简介](#1-项目简介)
- [2. 项目结构](#2-项目结构)
- [3. 功能特性](#3-功能特性)
- [4. 环境准备](#4-环境准备)
   - [4.1 Python 环境](#41-python-环境)
  - [4.2 创建并激活虚拟环境](#42-创建并激活虚拟环境)
  - [4.3 安装依赖](#43-安装依赖)
  - [4.4 配置 API 密钥](#44-配置-api-密钥)
- [5. 运行项目](#5-运行项目)
- [6. API 接口文档](#6-api-接口文档)
- [7. 技术框架与依赖](#7-技术框架与依赖)
- [8. 注意事项](#8-注意事项)
- [9. 体验地址](#9-体验地址)

---

## 1. 项目简介

Cyan Edition 是一个全栈聊天机器人应用，后端基于 FastAPI 提供 RESTful API 和 SSE（Server-Sent Events）流式响应，数据持久化使用 SQLite（可无缝切换至 PostgreSQL/MySQL）。前端采用 Vue 3 组合式 API，实现响应式界面、实时流式消息渲染、会话侧边栏、主题切换等现代 Web 体验。

核心能力：

* **多会话隔离，历史消息永久存储**

* **流式生成 AI 回复，首字延迟低**

* **支持多模型（豆包 Pro / Mini / Code、DeepSeek V3.2）**

* **可调节温度（0.0~2.0），控制回复随机性**

* **深色模式 / 浅色模式，本地持久化偏好**

* **Markdown 渲染 + 代码高亮（highlight.js）**

## 2. 项目结构

```plaintext
Cyan_Edition/
├── backend/                     # 后端服务目录
│   ├── config.py                # 加载 API Key 及初始化 Ark 客户端
│   ├── database.py              # SQLAlchemy 模型与数据库会话
│   ├── main.py                  # FastAPI 主程序（含所有 API 路由）
│   ├── requirements.txt         # Python 依赖清单
│   └── Key.env                  # API 密钥文件（需自行创建，勿提交）
├── frontend/                    # 前端静态资源目录
│   ├── index.html               # Vue 3 主页面模板
│   └── static/
│       ├── style.css            # 全局样式与动画
│       └── app.js               # Vue 3 组合式 API 业务逻辑
├── test_concurrent.py           # 并发测试脚本（可选）
├── chat.db                      # SQLite 数据库（自动生成）
└── README.md                    # 项目说明文档
```

## 3. 功能特性

* **精确问答匹配：** 对特定用户输入（如“韩信在干嘛”、“你好”）提供预设回复，响应速度快。

* **LLM 智能对话：** 用户问题无精确匹配时，转发给豆包 LLM，结合预设角色设定回复。

* **角色设定分离：** LLM 的角色设定存储在 `prompts.jsonl`，便于管理。

* **问答数据外部化：** 精确问答对存储在 `qa_data.jsonl`，便于维护。

* **跨域支持：** 已配置 CORS，方便前端开发调试。

## 4. 环境准备

在运行项目之前，请确保你的系统满足以下要求并完成必要的配置。

### 4.1 Python 环境

建议使用 **Python 3.8+**。

### 4.2 创建并激活虚拟环境

为了更好地管理项目依赖，强烈建议使用虚拟环境。

```bash
# 进入项目根目录
cd Cyan_Edition/

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境 (macOS/Linux)
source venv/bin/activate

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate

# 激活虚拟环境 (Windows)
.\venv\Scripts\activate
```

### 4.3 安装依赖
```bash
cd backend/
pip install -r requirements.txt

requirements.txt
fastapi
uvicorn
sqlalchemy
pydantic
python-dotenv
httpx
python-multipart
```
**注意：** 火山引擎 Ark SDK 由 volcenginesdkarkruntime 提供，已在 config.py 中导入，无需单独安装（若缺失可执行 pip install volcengine-python-sdk[ark]）。

### 4.4 配置 API 密钥
在项目根目录创建 .env 文件。
添加如下内容：
```bash
env
YOUR_API_KEY=你的火山引擎 Ark API Key
获取方式：登录火山引擎控制台，进入“模型推理” → “API Key 管理”创建。
```
config.py 会自动读取该文件并初始化 Ark 客户端。

## 5. 运行项目
```bash
cd backend
python main.py
```
服务默认在 http://localhost:5000 运行。


## 6. API 接口文档
### 6.1 获取会话列表
```bash
GET /api/conversations
response：[{ id, title, created_at }, ...]
```
#### 6.2 新建会话
```bash
POST /api/conversations/new
response：新建的会话对象。
```
#### 6.3 发送消息（流式）
```bash
POST /api/chat

json
{
  "messages": [
    { "role": "user", "content": "你好" },
    { "role": "assistant", "content": "你好！有什么可以帮助你的吗？" }
  ],
  "model_id": "xx-xx-xx",
  "conversation_id": 1,
  "temperature": 0.7
}
messages：完整对话历史（按时间升序）。
model_id：模型标识符（从 models 列表获取）。
conversation_id：可选，若为 null 则自动创建新会话。
temperature：可选，默认 0.7。

response：text/event-stream
data: {"content": "增量文本", "conv_id": 1}
```
#### 6.4 获取会话历史
```bash
GET /api/history/{conv_id}
response：[{ id, role, content, reasoning, created_at }, ...]
```
### 6.5 删除会话
```bash
DELETE /api/conversations/{conv_id}
response：{"status": "success"}
```

## 7. 技术框架与依赖
HTML5/CSS3/JavaScript
Tailwind CSS
jQuery
安装 Tailwind CSS（如需本地编译）：

```bash
npm install tailwindcss postcss autoprefixer --save-dev
```

## 8. 注意事项

## 9. 体验地址
https://dalonggou.xyz/
