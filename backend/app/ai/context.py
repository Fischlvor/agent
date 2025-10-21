"""
AI工具的上下文管理

使用 contextvars 在异步环境中传递数据库会话等上下文信息
这是Python标准的异步上下文传递方式
"""

from contextvars import ContextVar
from typing import Optional
from sqlalchemy.orm import Session

# ============ Context Variables ============

# 当前数据库会话
current_db_session: ContextVar[Optional[Session]] = ContextVar('db_session', default=None)

# 当前用户ID
current_user_id: ContextVar[Optional[int]] = ContextVar('user_id', default=None)

# 当前会话ID
current_session_id: ContextVar[Optional[str]] = ContextVar('session_id', default=None)


# ============ Helper Functions ============

def set_current_db_session(db: Session) -> None:
    """设置当前数据库会话"""
    current_db_session.set(db)


def get_current_db_session() -> Optional[Session]:
    """获取当前数据库会话"""
    return current_db_session.get()


def set_current_user_id(user_id: int) -> None:
    """设置当前用户ID"""
    current_user_id.set(user_id)


def get_current_user_id() -> Optional[int]:
    """获取当前用户ID"""
    return current_user_id.get()


def set_current_session_id(session_id: str) -> None:
    """设置当前会话ID"""
    current_session_id.set(session_id)


def get_current_session_id() -> Optional[str]:
    """获取当前会话ID"""
    return current_session_id.get()


def clear_context() -> None:
    """清除所有上下文（通常在请求结束时调用）"""
    current_db_session.set(None)
    current_user_id.set(None)
    current_session_id.set(None)

