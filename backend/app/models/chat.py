"""聊天消息模型定义"""

from datetime import datetime
from typing import Any, Dict

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ChatMessage(BaseModel):
    """聊天消息模型"""

    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="消息主键ID")
    message_id = Column(String(36), unique=True, nullable=False, comment="消息业务ID(UUID字符串)")
    session_id = Column(String(36),
                        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
                        nullable=False,
                        comment="关联的会话业务ID")
    parent_message_id = Column(String(36), nullable=True, comment="父消息业务ID")
    role = Column(String(20), nullable=True, comment="消息角色，如user、assistant、system、tool")
    content = Column(Text, nullable=True, comment="消息内容")
    message_type = Column(String(30), nullable=True, comment="消息类型，如text、image、file等")
    status = Column(String(20), nullable=True, comment="消息状态，如pending、sent、delivered、read、failed等")
    is_edited = Column(Boolean, default=False, comment="是否已编辑")
    is_deleted = Column(Boolean, default=False, comment="是否已删除")
    is_pinned = Column(Boolean, default=False, comment="是否置顶")
    is_summarized = Column(Boolean, default=False, comment="是否已被摘要覆盖")
    is_summary = Column(Boolean, default=False, comment="是否为摘要消息")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")
    delivered_at = Column(DateTime, nullable=True, comment="送达时间")
    read_at = Column(DateTime, nullable=True, comment="已读时间")
    model_name = Column(String(50), nullable=True, comment="使用的模型名称")
    prompt_tokens = Column(Integer, nullable=True, comment="提示词令牌数")
    completion_tokens = Column(Integer, nullable=True, comment="完成词令牌数")
    total_tokens = Column(Integer, nullable=True, comment="总令牌数")
    generation_time = Column(Float, nullable=True, comment="生成时间（秒）")
    structured_content = Column(JSON, nullable=True, comment="结构化内容，JSON格式")
    attachments = Column(JSON, nullable=True, comment="附件信息，JSON格式")
    user_rating = Column(Integer, nullable=True, comment="用户评分（1-5）")
    user_feedback = Column(Text, nullable=True, comment="用户反馈")
    message_metadata = Column(JSON, nullable=True, comment="元数据，JSON格式")
    error_info = Column(JSON, nullable=True, comment="错误信息，JSON格式")

    # 关系
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        """返回消息的字符串表示"""
        return f"<ChatMessage {self.id} role={self.role}>"  # pylint: disable=no-member

    @property
    def is_user_message(self) -> bool:
        """判断是否为用户消息"""
        return self.role == "user"

    @property
    def is_assistant_message(self) -> bool:
        """判断是否为助手消息"""
        return self.role == "assistant"

    @property
    def is_system_message(self) -> bool:
        """判断是否为系统消息"""
        return self.role == "system"

    @property
    def is_tool_message(self) -> bool:
        """判断是否为工具消息"""
        return self.role == "tool"

    def mark_as_read(self) -> None:
        """标记消息为已读"""
        if not self.read_at:
            self.read_at = datetime.utcnow()

    def mark_as_delivered(self) -> None:
        """标记消息为已送达"""
        if not self.delivered_at:
            self.delivered_at = datetime.utcnow()

    def edit_content(self, new_content: str) -> None:
        """编辑消息内容"""
        self.content = new_content
        self.is_edited = True

    def to_dict(self) -> Dict[str, Any]:
        """将消息转换为字典"""
        message_dict = super().to_dict()

        # 添加计算属性
        message_dict["is_user_message"] = self.is_user_message
        message_dict["is_assistant_message"] = self.is_assistant_message
        message_dict["is_system_message"] = self.is_system_message
        message_dict["is_tool_message"] = self.is_tool_message

        return message_dict
