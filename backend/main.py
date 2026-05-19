import os, uuid, json
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

# 导入数据库配置和 AI 客户端实例
from database import init_db, get_db, Conversation, Message
from config import client 

# 初始化 FastAPI 应用，定义系统名称
app = FastAPI(title="Cyan Edition - Persistent Chat")

# --- 跨域配置 ---
# 允许前端和后端分离时跨域通信，允许所有来源、方法和请求头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    """应用启动回调：启动时确保数据库已初始化并创建所需表格"""
    init_db()
    print("系统已启动，数据库连接成功。")

# --- 数据验证模型定义 ---
class ChatMessage(BaseModel):
    """单条消息的载体结构，role 为 'user' 或 'assistant'，content 为消息文本"""
    role: str
    content: str

class ChatRequest(BaseModel):
    """对话请求完整数据结构，包含对话历史、模型ID、会话ID、温度参数"""
    messages: List[ChatMessage]           # 对话历史，按时间升序排列
    model_id: str                         # 选用的模型标识
    conversation_id: Optional[int] = None # 会话ID，为空则新建会话
    temperature: float = 0.7              # 温度参数，默认0.7，范围由Pydantic校验保障

# --- 核心 API 接口定义 ---

@app.get("/api/conversations")
async def list_conversations(db: Session = Depends(get_db)):
    """获取侧边栏的会话列表，按照创建时间倒序返回"""
    return db.query(Conversation).order_by(Conversation.created_at.desc()).all()

@app.post("/api/conversations/new")
async def create_new_conversation(db: Session = Depends(get_db)):
    """新建对话：在数据库生成占位会话，返回会话对象供前端立即使用"""
    try:
        new_conv = Conversation(title="新对话")
        db.add(new_conv)
        db.commit()
        db.refresh(new_conv)
        return new_conv
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat(req: ChatRequest, db: Session = Depends(get_db)):
    """
    核心对话接口：
    1. 处理会话创建或续接
    2. 持久化用户消息
    3. 调用大模型生成 SSE 流式响应
    4. 流结束后持久化 AI 完整回复
    """
    try:
        # 输出请求关键信息，便于调试
        print(f"\n[请求到达] 收到对话请求 | 当前响应模型: {req.model_id} | 接收到的前端温度参数: {req.temperature}")

        # 会话管理：携带 conversation_id 则查找现有会话，否则新建
        if req.conversation_id:
            conv = db.query(Conversation).filter(Conversation.id == req.conversation_id).first()
            # 如果提供的会话ID不存在，可在此处添加异常处理（当前直接使用查询结果，可能为None）
        else:
            conv = Conversation(title=req.messages[-1].content[:20])  # 用首条消息前20字符作为临时标题
            db.add(conv)
            db.commit()
            db.refresh(conv)

        # 智能标题更替：若标题仍为默认的"新对话"，则替换为首条用户消息的前20字符
        if conv and conv.title == "新对话" and len(req.messages) > 0:
            conv.title = req.messages[0].content[:20]
            db.commit()

        # 持久化用户最新消息
        user_input = req.messages[-1].content
        db.add(Message(conversation_id=conv.id, role="user", content=user_input))
        db.commit()

        def sse_generator():
            """同步生成器，用于迭代产出 SSE 事件流"""
            # 将消息列表转换为大模型 API 要求的格式
            llm_messages = [{"role": m.role, "content": m.content} for m in req.messages]
            
            # 以流式模式调用大模型
            completion = client.chat.completions.create(
                model=req.model_id, 
                messages=llm_messages,
                temperature=req.temperature, 
                stream=True
            )
            
            print(f"【后端验证】已开启 SSE 流，当前模型温度: {req.temperature}")
            
            full_text = ""  # 累积完整回复文本
            for chunk in completion:
                # 提取每次增量内容
                if chunk.choices and chunk.choices[0].delta.content:
                    delta = chunk.choices[0].delta.content
                    full_text += delta
                    # 封装为 SSE 标准格式：data: {json}\n\n
                    yield f"data: {json.dumps({'content': delta, 'conv_id': conv.id})}\n\n"
            
            # 流式传输结束后，将完整 AI 回复持久化到数据库
            db.add(Message(conversation_id=conv.id, role="assistant", content=full_text))
            db.commit()

        # 返回 StreamingResponse，媒体类型设置为 text/event-stream
        return StreamingResponse(sse_generator(), media_type="text/event-stream")
    except Exception as e:
        # 出现异常时回滚数据库，避免数据不一致
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversations/{conv_id}")
async def delete_conversation(conv_id: int, db: Session = Depends(get_db)):
    """删除指定会话及其所有关联消息"""
    try:
        # 先删除该会话下的所有消息
        db.query(Message).filter(Message.conversation_id == conv_id).delete()
        # 再删除会话本身
        db.query(Conversation).filter(Conversation.id == conv_id).delete()
        db.commit()
        return {"status": "success"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history/{conv_id}")
async def get_history(conv_id: int, db: Session = Depends(get_db)):
    """加载指定会话的历史消息记录"""
    return db.query(Message).filter(Message.conversation_id == conv_id).all()

# --- 静态资源托管与页面分发逻辑 ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)          # 项目根目录
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")  # 前端静态文件目录

# 挂载静态资源目录，注意必须优先于根路由定义
app.mount("/static", StaticFiles(directory=os.path.join(FRONTEND_DIR, "static")), name="static")
app.mount("/uploads", StaticFiles(directory=os.path.join(PROJECT_ROOT, "uploads")), name="uploads")

# 根路由返回前端主页面
@app.get("/")
async def index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

if __name__ == "__main__":
    import uvicorn
    # 启动服务，监听本地5000端口
    uvicorn.run(app, host="127.0.0.1", port=5000)