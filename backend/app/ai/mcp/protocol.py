"""
真正的 MCP 协议实现

基于官方 Model Context Protocol 规范：
- JSON-RPC 2.0 通信协议
- 资源（Resources）
- 工具（Tools）
- 提示（Prompts）

参考: https://modelcontextprotocol.io/
"""

from typing import Dict, Any, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


# ============ JSON-RPC 2.0 基础协议 ============

class JSONRPCRequest(BaseModel):
    """JSON-RPC 2.0 请求"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    """JSON-RPC 2.0 响应"""
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None


class JSONRPCError(BaseModel):
    """JSON-RPC 2.0 错误"""
    code: int
    message: str
    data: Optional[Any] = None


# ============ MCP 核心类型 ============

class ResourceType(str, Enum):
    """资源类型"""
    TEXT = "text"
    BINARY = "binary"


class ToolParameter(BaseModel):
    """工具参数定义"""
    type: str
    description: Optional[str] = None
    required: bool = False
    enum: Optional[List[Any]] = None
    properties: Optional[Dict[str, "ToolParameter"]] = None


class ToolDefinition(BaseModel):
    """MCP 工具定义"""
    name: str
    description: str
    inputSchema: Dict[str, Any] = Field(
        description="JSON Schema defining the tool's parameters"
    )


class ToolCallRequest(BaseModel):
    """工具调用请求"""
    name: str
    arguments: Dict[str, Any]


class ToolCallResult(BaseModel):
    """工具调用结果"""
    content: List[Dict[str, Any]]  # 可以包含多个内容块
    isError: bool = False


class Resource(BaseModel):
    """MCP 资源"""
    uri: str  # 唯一标识符
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = None


class ResourceContent(BaseModel):
    """资源内容"""
    uri: str
    mimeType: Optional[str] = None
    text: Optional[str] = None  # 文本资源
    blob: Optional[str] = None  # 二进制资源（base64）


class Prompt(BaseModel):
    """MCP 提示模板"""
    name: str
    description: Optional[str] = None
    arguments: Optional[List[Dict[str, Any]]] = None


# ============ MCP 协议消息 ============

class InitializeRequest(BaseModel):
    """初始化请求"""
    protocolVersion: str
    capabilities: Dict[str, Any]
    clientInfo: Dict[str, str]


class InitializeResult(BaseModel):
    """初始化响应"""
    protocolVersion: str
    capabilities: Dict[str, Any]
    serverInfo: Dict[str, str]


class ListToolsResult(BaseModel):
    """列出工具的响应"""
    tools: List[ToolDefinition]


class ListResourcesResult(BaseModel):
    """列出资源的响应"""
    resources: List[Resource]


class ListPromptsResult(BaseModel):
    """列出提示的响应"""
    prompts: List[Prompt]


# ============ MCP 事件 ============

class ProgressNotification(BaseModel):
    """进度通知"""
    progressToken: Union[str, int]
    progress: float
    total: Optional[float] = None


class LoggingLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogMessage(BaseModel):
    """日志消息"""
    level: LoggingLevel
    logger: Optional[str] = None
    data: Any


# ============ MCP 方法名常量 ============

class MCPMethod:
    """MCP 标准方法名"""
    # 初始化
    INITIALIZE = "initialize"
    INITIALIZED = "notifications/initialized"

    # 工具相关
    TOOLS_LIST = "tools/list"
    TOOLS_CALL = "tools/call"

    # 资源相关
    RESOURCES_LIST = "resources/list"
    RESOURCES_READ = "resources/read"
    RESOURCES_SUBSCRIBE = "resources/subscribe"
    RESOURCES_UNSUBSCRIBE = "resources/unsubscribe"

    # 提示相关
    PROMPTS_LIST = "prompts/list"
    PROMPTS_GET = "prompts/get"

    # 通知
    NOTIFICATION_PROGRESS = "notifications/progress"
    NOTIFICATION_MESSAGE = "notifications/message"
    NOTIFICATION_RESOURCES_UPDATED = "notifications/resources/updated"


# ============ 辅助类型 ============

class ServerCapabilities(BaseModel):
    """服务器能力声明"""
    tools: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Server supports tool calls"
    )
    resources: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Server exposes resources"
    )
    prompts: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Server provides prompts"
    )
    logging: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Server supports logging"
    )


class ClientCapabilities(BaseModel):
    """客户端能力声明"""
    experimental: Optional[Dict[str, Any]] = None
    roots: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Client can provide root directories"
    )


# 更新 ToolParameter 的前向引用
ToolParameter.model_rebuild()

