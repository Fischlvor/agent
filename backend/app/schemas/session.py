"""会话相关的Schema定义。"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SessionBase(BaseModel):
    """会话基础Schema"""
    title: Optional[str] = None
    description: Optional[str] = None


class SessionCreate(SessionBase):
    """创建会话的请求Schema"""


class SessionUpdate(SessionBase):
    """更新会话的请求Schema"""


class SessionResponse(SessionBase):
    """会话的响应Schema"""
    id: int
    session_id: Optional[UUID] = None  # 直接使用 UUID 类型，Pydantic 自动序列化为 JSON 字符串
    created_at: datetime
    last_activity_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        """Pydantic配置"""
        from_attributes = True
