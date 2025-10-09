"""会话模型定义"""

from typing import Any, Dict, List, TYPE_CHECKING

from sqlalchemy import (Boolean, Column, DateTime, Float, ForeignKey, Integer,
                        JSON, String, Text)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.chat import ChatMessage


class ChatSession(BaseModel):
    """聊天会话模型"""

    __tablename__ = "chat_sessions"

    id = Column(Integer,
                primary_key=True,
                autoincrement=True,
                comment="会话主键ID")
    session_id = Column(String(36),
                        unique=True,
                        nullable=False,
                        comment="会话业务ID(UUID字符串)")
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的用户ID",
    )
    title = Column(String(200), nullable=True, comment="会话标题")
    description = Column(Text, nullable=True, comment="会话描述")
    status = Column(String(20),
                    nullable=True,
                    comment="会话状态，如active、archived等")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    last_activity_at = Column(DateTime, nullable=True, comment="最后活动时间")
    message_count = Column(Integer, default=0, comment="消息数量")
    total_tokens = Column(Integer, default=0, comment="总令牌数")
    current_context_tokens = Column(Integer, default=0, comment="当前上下文令牌数")
    ai_model = Column(String(50), nullable=True, comment="使用的AI模型")
    temperature = Column(Float, default=0.7, comment="AI模型温度参数")
    max_tokens = Column(Integer, default=4000, comment="最大令牌数限制")
    context_data = Column(JSON, nullable=True, comment="上下文数据，JSON格式")
    system_prompt = Column(Text, nullable=True, comment="系统提示词")
    session_metadata = Column(JSON, nullable=True, comment="元数据，JSON格式")
    tags = Column(JSON, nullable=True, comment="标签，JSON格式")

    # 关系
    messages = relationship("ChatMessage",
                            back_populates="session",
                            cascade="all, delete-orphan")
    user = relationship("User", backref="sessions")

    def __repr__(self) -> str:
        """返回会话的字符串表示"""
        return f"<ChatSession {self.title or self.id}>"  # pylint: disable=no-member

    def add_message(self, message_data: Dict[str, Any]) -> "ChatMessage":
        """添加消息到会话"""
        # 动态导入避免循环导入
        from app.models.chat import ChatMessage  # pylint: disable=import-outside-toplevel

        message = ChatMessage(**message_data)
        message.session_id = self.id  # pylint: disable=no-member
        self.messages.append(message)
        self.message_count += 1
        self.last_activity_at = message.created_at

        # 更新令牌计数
        if message.total_tokens:
            self.total_tokens += message.total_tokens

        return message

    def get_messages(self,
                     limit: int = 50,
                     skip: int = 0) -> List["ChatMessage"]:
        """获取会话的消息"""
        return sorted(
            [msg for msg in self.messages if not msg.is_deleted],
            key=lambda x: x.created_at,
        )[skip:skip + limit]

    # 重写父类方法，添加新参数
    # pylint: disable=arguments-differ
    def to_dict(self, include_messages: bool = False) -> Dict[str, Any]:
        """将会话转换为字典，可选是否包含消息

        Args:
            include_messages: 是否包含消息

        Returns:
            会话信息字典
        """
        session_dict = super().to_dict()

        if include_messages:
            session_dict["messages"] = [
                msg.to_dict() for msg in self.get_messages()
            ]

        return session_dict
