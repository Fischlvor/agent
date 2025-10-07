"""
ADK Session Service 适配器

创建最小化的 SessionService，满足 ADK Runner 的要求
"""

from typing import Optional, Dict, Any
from google.adk.sessions import BaseSessionService, Session
from google.adk.sessions.base_session_service import GetSessionConfig, ListSessionsResponse
from google.genai.types import Content
import uuid


class SimpleSessionService(BaseSessionService):
    """
    简化的会话服务（内存版）

    只为满足 ADK Runner 的基本要求
    """

    def __init__(self):
        """初始化会话服务"""
        self._sessions: Dict[str, Session] = {}

    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None
    ) -> Session:
        """
        创建新会话

        Args:
            app_name: 应用名称
            user_id: 用户ID
            state: 会话状态
            session_id: 会话ID（可选，如果不提供则生成）

        Returns:
            新创建的会话对象
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        key = f"{app_name}:{user_id}:{session_id}"

        new_session = Session(
            id=session_id,  # ✅ 正确的字段名
            app_name=app_name,  # ✅ 必需字段
            user_id=user_id,  # ✅ 正确
            state=state or {},  # ✅ 正确
            events=[]  # ✅ 正确的字段名（不是 history）
        )

        self._sessions[key] = new_session
        return new_session

    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None
    ) -> Optional[Session]:
        """
        获取会话

        Args:
            app_name: 应用名称
            user_id: 用户ID
            session_id: 会话ID
            config: 获取配置

        Returns:
            会话对象，如果不存在则返回 None
        """
        key = f"{app_name}:{user_id}:{session_id}"

        # 如果不存在，自动创建
        if key not in self._sessions:
            return await self.create_session(
                app_name=app_name,
                user_id=user_id,
                session_id=session_id
            )

        return self._sessions[key]

    async def delete_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str
    ) -> None:
        """
        删除会话

        Args:
            app_name: 应用名称
            user_id: 用户ID
            session_id: 会话ID
        """
        key = f"{app_name}:{user_id}:{session_id}"
        if key in self._sessions:
            del self._sessions[key]

    async def list_sessions(
        self,
        *,
        app_name: str,
        user_id: str
    ) -> ListSessionsResponse:
        """
        列出用户的所有会话

        Args:
            app_name: 应用名称
            user_id: 用户ID

        Returns:
            会话列表响应
        """
        sessions = [
            session for key, session in self._sessions.items()
            if key.startswith(f"{app_name}:{user_id}:")
        ]

        return ListSessionsResponse(sessions=sessions)


def create_simple_session_service() -> SimpleSessionService:
    """
    工厂函数：创建简化的会话服务

    Returns:
        SimpleSessionService 实例
    """
    return SimpleSessionService()

