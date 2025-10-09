"""AI模型配置模型定义"""

from typing import Any, Dict

from sqlalchemy import Boolean, Column, Integer, JSON, String, Text

from app.models.base import BaseModel


class AIModel(BaseModel):
    """AI模型配置模型"""

    __tablename__ = "ai_models"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="模型主键ID")
    name = Column(String(100), nullable=False, comment="模型显示名称")
    model_id = Column(String(100), nullable=False, unique=True, comment="模型ID")
    provider = Column(String(50), nullable=False, comment="模型提供商")
    base_url = Column(String(255), nullable=False, comment="API基础URL")
    description = Column(Text, nullable=True, comment="模型描述")
    max_tokens = Column(Integer, default=8192, comment="最大token数")
    max_context_length = Column(Integer, default=32768, comment="最大上下文长度")
    supports_streaming = Column(Boolean, default=True, comment="是否支持流式输出")
    supports_tools = Column(Boolean, default=True, comment="是否支持工具调用")
    is_active = Column(Boolean, default=True, comment="是否启用")
    icon_url = Column(String(500), nullable=True, comment="模型图标URL")
    display_order = Column(Integer, default=0, comment="显示顺序")
    config = Column(JSON, nullable=True, comment="额外配置，JSON格式")

    def __repr__(self) -> str:
        """返回模型的字符串表示"""
        return f"<AIModel {self.name} ({self.model_id})>"
