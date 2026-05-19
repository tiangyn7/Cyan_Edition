# backend/database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

SQLALCHEMY_DATABASE_URL = "sqlite:///./chat.db"

# connect_args={"check_same_thread": False} 是 SQLite 必须的配置
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 模型定义 ---
class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, default="新对话")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String) # user / assistant
    content = Column(Text)
    reasoning = Column(Text, nullable=True) # 存储深度思考
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

# 创建表
def init_db():
    Base.metadata.create_all(bind=engine)

# 获取数据库会话的工具函数
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()