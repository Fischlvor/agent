"""调用记录模型定义"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db import Base


class ModelInvocation(Base):
    """LLM调用记录模型"""

    __tablename__ = "model_invocations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="调用记录主键ID")
    message_id = Column(
        String(36),
        ForeignKey("chat_messages.message_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的消息业务ID"
    )
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的会话业务ID"
    )
    sequence_number = Column(Integer, nullable=False, comment="第几次LLM调用")
    prompt_tokens = Column(Integer, nullable=False, comment="输入token数")
    completion_tokens = Column(Integer, nullable=False, comment="输出token数")
    total_tokens = Column(Integer, nullable=False, comment="总token数")
    duration_ms = Column(Integer, nullable=True, comment="调用耗时（毫秒）")
    model_name = Column(String(100), nullable=True, comment="模型名称")
    finish_reason = Column(String(50), nullable=True, comment="完成原因")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    # 关系
    message = relationship("ChatMessage", foreign_keys=[message_id])
    session = relationship("ChatSession", foreign_keys=[session_id])

    def __repr__(self) -> str:
        """返回调用记录的字符串表示"""
        return f"<ModelInvocation {self.id} seq={self.sequence_number} tokens={self.total_tokens}>"


class ToolInvocation(Base):
    """工具调用记录模型"""

    __tablename__ = "tool_invocations"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="调用记录主键ID")
    message_id = Column(
        String(36),
        ForeignKey("chat_messages.message_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的消息业务ID"
    )
    session_id = Column(
        String(36),
        ForeignKey("chat_sessions.session_id", ondelete="CASCADE"),
        nullable=False,
        comment="关联的会话业务ID"
    )
    sequence_number = Column(Integer, nullable=False, comment="第几次工具调用")
    triggered_by_llm_sequence = Column(Integer, nullable=True, comment="由第几次LLM调用触发")
    tool_name = Column(String(100), nullable=False, comment="工具名称")
    arguments = Column(JSON, nullable=True, comment="输入参数")
    result = Column(Text, nullable=True, comment="执行结果")
    status = Column(String(20), nullable=False, comment="执行状态")
    cache_hit = Column(Boolean, nullable=False, default=False, comment="是否命中缓存")
    error_message = Column(Text, nullable=True, comment="错误信息")
    duration_ms = Column(Integer, nullable=True, comment="执行耗时（毫秒）")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, comment="创建时间")

    # 关系
    message = relationship("ChatMessage", foreign_keys=[message_id])
    session = relationship("ChatSession", foreign_keys=[session_id])

    def __repr__(self) -> str:
        """返回调用记录的字符串表示"""
        return f"<ToolInvocation {self.id} seq={self.sequence_number} tool={self.tool_name}>"

