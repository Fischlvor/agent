"""调用记录Schema定义"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ModelInvocationBase(BaseModel):
    """LLM调用记录基础Schema"""

    sequence_number: int = Field(..., description="第几次LLM调用")
    prompt_tokens: int = Field(..., description="输入token数")
    completion_tokens: int = Field(..., description="输出token数")
    total_tokens: int = Field(..., description="总token数")
    duration_ms: Optional[int] = Field(None, description="调用耗时（毫秒）")
    model_name: Optional[str] = Field(None, description="模型名称")
    finish_reason: Optional[str] = Field(None, description="完成原因")


class ModelInvocationCreate(ModelInvocationBase):
    """创建LLM调用记录的Schema"""

    message_id: str = Field(..., description="关联的消息ID")
    session_id: str = Field(..., description="关联的会话ID")


class ModelInvocationResponse(ModelInvocationBase):
    """LLM调用记录响应Schema"""

    id: int = Field(..., description="调用记录ID")
    message_id: str = Field(..., description="关联的消息ID")
    session_id: str = Field(..., description="关联的会话ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        """Pydantic配置"""
        from_attributes = True


class ToolInvocationBase(BaseModel):
    """工具调用记录基础Schema"""

    sequence_number: int = Field(..., description="第几次工具调用")
    triggered_by_llm_sequence: Optional[int] = Field(None, description="由第几次LLM调用触发")
    tool_name: str = Field(..., description="工具名称")
    arguments: Optional[Dict[str, Any]] = Field(None, description="输入参数")
    result: Optional[str] = Field(None, description="执行结果")
    status: str = Field(..., description="执行状态")
    cache_hit: bool = Field(False, description="是否命中缓存")
    error_message: Optional[str] = Field(None, description="错误信息")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")


class ToolInvocationCreate(ToolInvocationBase):
    """创建工具调用记录的Schema"""

    message_id: str = Field(..., description="关联的消息ID")
    session_id: str = Field(..., description="关联的会话ID")


class ToolInvocationResponse(ToolInvocationBase):
    """工具调用记录响应Schema"""

    id: int = Field(..., description="调用记录ID")
    message_id: str = Field(..., description="关联的消息ID")
    session_id: str = Field(..., description="关联的会话ID")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        """Pydantic配置"""
        from_attributes = True


class InvocationStatsResponse(BaseModel):
    """调用统计响应Schema"""

    total_invocations: int = Field(..., description="总调用次数")
    total_tokens: int = Field(..., description="总token数")
    avg_duration_ms: float = Field(..., description="平均耗时（毫秒）")
    total_duration_ms: int = Field(..., description="总耗时（毫秒）")


class ToolUsageStatsResponse(BaseModel):
    """工具使用统计响应Schema"""

    tool_name: str = Field(..., description="工具名称")
    total_calls: int = Field(..., description="总调用次数")
    success_count: int = Field(..., description="成功次数")
    error_count: int = Field(..., description="失败次数")
    cached_count: int = Field(..., description="缓存命中次数")
    success_rate: float = Field(..., description="成功率")
    cache_hit_rate: float = Field(..., description="缓存命中率")
    avg_duration_ms: float = Field(..., description="平均耗时（毫秒）")

