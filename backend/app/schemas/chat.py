"""聊天相关的Schema定义。"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============ AI模型相关 ============

class AIModelResponse(BaseModel):
    """AI模型响应Schema"""
    model_config = {
        "protected_namespaces": (),  # 禁用 model_ 命名空间保护
        "from_attributes": True  # 支持从ORM对象创建
    }

    id: int
    name: str
    model_id: str
    provider: str
    base_url: str
    description: Optional[str] = None
    max_tokens: int
    supports_streaming: bool
    supports_tools: bool
    is_active: bool
    icon_url: Optional[str] = None
    display_order: int
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime


# ============ 会话相关 ============

class SessionCreate(BaseModel):
    """创建会话的请求Schema"""
    title: Optional[str] = Field(None, description="会话标题")
    ai_model: Optional[str] = Field("qwen3:8b", description="使用的AI模型")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(0.7, ge=0, le=2, description="温度参数")
    max_tokens: Optional[int] = Field(4000, gt=0, description="最大令牌数")


class SessionUpdate(BaseModel):
    """更新会话的请求Schema"""
    title: Optional[str] = Field(None, description="会话标题")
    is_pinned: Optional[bool] = Field(None, description="是否置顶")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="温度参数")
    ai_model: Optional[str] = Field(None, description="AI模型")


class SessionResponse(BaseModel):
    """会话响应Schema"""
    model_config = {"from_attributes": True}

    id: int
    session_id: Optional[str] = None
    user_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    is_pinned: bool = False
    last_activity_at: Optional[datetime] = None
    message_count: int = 0
    total_tokens: int = 0
    current_context_tokens: int = 0
    ai_model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4000
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # 计算属性
    max_context_tokens: Optional[int] = Field(None, description="模型最大上下文长度")
    context_usage_percent: Optional[float] = Field(None, description="上下文使用百分比")


class SessionListResponse(BaseModel):
    """会话列表响应Schema（游标分页）"""
    sessions: List[SessionResponse]
    next_cursor: Optional[datetime] = Field(None, description="下一页游标")
    has_more: bool = Field(False, description="是否还有更多数据")


# ============ 消息相关 ============

class MessageCreate(BaseModel):
    """创建消息的请求Schema（通过HTTP POST发送，响应通过WebSocket流式返回）"""
    model_config = {"protected_namespaces": ()}  # 禁用 model_ 命名空间保护

    content: str = Field(..., description="消息内容")
    model_id: Optional[str] = Field(None, description="使用的模型ID")
    parent_message_id: Optional[str] = Field(None, description="父消息ID（用于编辑消息时的关联）")


class MessageUpdate(BaseModel):
    """更新消息的请求Schema"""
    content: str = Field(..., description="新的消息内容")


class MessageResponse(BaseModel):
    """消息响应Schema"""
    model_config = {
        "protected_namespaces": (),  # 禁用 model_ 命名空间保护
        "from_attributes": True  # 支持从ORM对象创建
    }

    id: int
    message_id: Optional[str] = None
    session_id: str
    parent_message_id: Optional[str] = None
    role: str
    content: Optional[str] = None
    message_type: Optional[str] = None
    status: Optional[str] = None
    is_edited: bool = False
    is_deleted: bool = False
    is_pinned: bool = False
    sent_at: Optional[datetime] = None
    model_name: Optional[str] = None
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    generation_time: Optional[float] = None
    structured_content: Optional[Dict[str, Any]] = None
    user_rating: Optional[int] = None
    user_feedback: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class MessageListResponse(BaseModel):
    """消息列表响应Schema"""
    messages: List[MessageResponse]
    total: int


# ============ WebSocket消息 ============

class WSMessageSend(BaseModel):
    """WebSocket发送消息请求"""
    model_config = {"protected_namespaces": ()}  # 禁用 model_ 命名空间保护

    type: str = Field("send_message", description="消息类型")
    session_id: str = Field(..., description="会话ID")
    content: str = Field(..., description="消息内容")
    model_id: Optional[str] = Field(None, description="模型ID")


class WSMessageStop(BaseModel):
    """WebSocket停止生成请求"""
    type: str = Field("stop_generation", description="消息类型")
    session_id: str = Field(..., description="会话ID")


class WSMessagePing(BaseModel):
    """WebSocket心跳请求"""
    type: str = Field("ping", description="消息类型")


class WSMessagePong(BaseModel):
    """WebSocket心跳响应"""
    type: str = Field("pong", description="消息类型")


class WSMessageStart(BaseModel):
    """WebSocket开始生成响应"""
    type: str = Field("start", description="消息类型")
    message_id: str = Field(..., description="消息ID")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(2000, description="事件类型代码")


class WSMessageThinkingStart(BaseModel):
    """WebSocket思考开始"""
    type: str = Field("thinking_start", description="消息类型")
    thinking_id: str = Field(..., description="思考块ID")
    status: str = Field("深度思考中", description="状态消息")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(3000, description="事件类型代码")


class WSMessageThinkingDelta(BaseModel):
    """WebSocket思考状态（流式增量）"""
    type: str = Field("thinking_delta", description="消息类型")
    thinking_id: str = Field(..., description="思考块ID")
    delta: str = Field(..., description="思考增量内容")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(3001, description="事件类型代码")


class WSMessageThinkingComplete(BaseModel):
    """WebSocket思考完成（只发送状态标识）"""
    type: str = Field("thinking_complete", description="消息类型")
    thinking_id: str = Field(..., description="思考块ID")
    status: str = Field("已完成思考", description="状态消息")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(3002, description="事件类型代码")


class WSMessageThinking(BaseModel):
    """WebSocket思考状态（兼容旧版本，已废弃）"""
    type: str = Field("thinking", description="消息类型")
    message: str = Field("正在思考...", description="状态消息")


class WSMessageToolCall(BaseModel):
    """WebSocket工具调用"""
    type: str = Field("tool_call", description="消息类型")
    tool_name: str = Field(..., description="工具名称")
    tool_args: Dict[str, Any] = Field(..., description="工具参数")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(4000, description="事件类型代码")


class WSMessageToolResult(BaseModel):
    """WebSocket工具结果"""
    type: str = Field("tool_result", description="消息类型")
    tool_name: str = Field(..., description="工具名称")
    result: Any = Field(..., description="工具结果")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(4001, description="事件类型代码")


class WSMessageContent(BaseModel):
    """WebSocket内容流"""
    type: str = Field("content", description="消息类型")
    delta: str = Field(..., description="增量内容")
    content: Optional[str] = Field(None, description="累积内容（已废弃，前端自行拼接）")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(2001, description="事件类型代码")


class WSMessageDone(BaseModel):
    """WebSocket生成完成"""
    type: str = Field("done", description="消息类型")
    message_id: str = Field(..., description="消息ID")
    total_tokens: Optional[int] = Field(None, description="总令牌数")
    prompt_tokens: Optional[int] = Field(None, description="提示令牌数")
    completion_tokens: Optional[int] = Field(None, description="完成令牌数")
    generation_time: Optional[float] = Field(None, description="生成时间（秒）")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(2002, description="事件类型代码")


class WSMessageError(BaseModel):
    """WebSocket错误"""
    type: str = Field("error", description="消息类型")
    error: str = Field(..., description="错误信息")
    event_id: int = Field(..., description="事件序列号（自增）")
    event_type: int = Field(1999, description="事件类型代码")
