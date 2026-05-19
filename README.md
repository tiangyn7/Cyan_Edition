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
- [5. 数据文件准备](#5-数据文件准备)
  - [5.1 qa_data.jsonl (精确问答数据)](#51-qa_datajsonl-精确问答数据)
  - [5.2 prompts.jsonl (LLM 系统指令)](#52-promptsjsonl-llm-系统指令)
- [6. 运行项目](#6-运行项目)
- [7. 体验地址](#7-体验地址)
- [8. 技术框架与依赖](#8-技术框架与依赖)
  - [8.1 后端依赖（Python）](#81-后端依赖python)
  - [8.2 前端依赖](#82-前端依赖)
  - [8.3 数据依赖](#83-数据依赖)
- [9. API 接口说明](#9-api-接口说明)
- [10. 注意事项](#10-注意事项)

---

## 1. 项目简介

这是一个基于 Flask 构建的简单聊天机器人后端服务，集成了精确问答匹配和大型语言模型（LLM）调用功能。它旨在提供一个灵活的聊天体验，既能对预设问题进行精准应答，也能调用 LLM 智能回复。

## 2. 项目结构

```plaintext
ML-AI-CHAT/
├── .env               # 存储敏感环境变量（如 API 密钥），请勿提交到 Git!
├── README.md          # 项目主说明文档（当前文件）
├── backend/           # Flask 后端应用代码
│   ├── app.py
│   ├── config.py
│   └── requirements.txt
├── data/              # 存储 LLM 相关的 JSONL 数据文件
│   ├── qa_data.jsonl
│   └── prompts.jsonl
├── frontend/          # 网页界面文件
│   ├── index.html
│   └── ... (其他前端资源，如 CSS/JS)
└── venv/              # Python 虚拟环境，请勿提交到 Git!
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
cd ML-AI-CHAT/

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
```

### 4.4 配置 API 密钥
在项目根目录创建 .env 文件。
添加如下内容：
```bash
env
DOUBAO_API_KEY="YOUR_API_KEY"
确保 config.py 能正确读取该变量（示例）：
Python
import os
from dotenv import load_dotenv
from doubao.client import DoubaoClient

load_dotenv()
DOUBAO_API_KEY = os.getenv("YOUR_API_KEY")
client = DoubaoClient(api_key=YOUR_API_KEYY)
```

## 5. 数据文件准备
在 data/ 目录下，确保以下两个 .jsonl 文件：

### 5.1 qa_data.jsonl (精确问答数据)
每行一个 JSON 对象，包含 query 和 response 字段。例如：
```bash
JSON
{"query": "你好", "response": "111！我是AG超玩会梦泪，扣1送地狱火！"}
5.2 prompts.jsonl (LLM 系统指令)
每行一个 JSON 对象，包含 LLM 角色设定。例如：

JSON
{"role": "system", "content": "你是AG超玩会梦泪。你会用夸张表情和游戏梗互动，用直播互动话术回应粉丝，用简洁游戏术语解决问题，用直播整活话术回应粉丝。"}
```

## 6. 运行项目

# 激活虚拟环境（如未激活）
```bash
cd backend/
python app.py
```
服务默认在 http://0.0.0.0:5000 运行。

前端页面：浏览器打开 frontend/index.html，或通过前端服务器访问。

## 7. 体验地址
https://dalonggou.xyz/

## 8. 技术框架与依赖
### 8.1 后端依赖（Python）
#### Flask
##### python-dotenv
##### Flask-CORS
##### requests
安装：

```bash
pip install -r requirements.txt
```
### 8.2 前端依赖
HTML5/CSS3/JavaScript
Tailwind CSS
jQuery
安装 Tailwind CSS（如需本地编译）：

```bash
npm install tailwindcss postcss autoprefixer --save-dev
```
### 8.3 数据依赖
JSONL 文件格式（qa_data.jsonl、prompts.jsonl）


## 9. API 接口说明
```bash
POST /api/chat

请求体（JSON）：
JSON
{
    "message": "用户输入的消息"
}
响应体（JSON）：
成功：

JSON
{
    "message": "AI 或预设的回复",
    "status": "success"
}
错误：

JSON
{
    "error": "错误信息",
    "status": "error"
}
```
## 10. 注意事项
#### 生产环境建议配置 Nginx 或其他反向代理处理跨域和 HTTPS。确保 config.py 能正确从 .env 文件加载 YOUR_API_KEY。
#### 阅读模型官方引擎文档，配置必要的SDK
