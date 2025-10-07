"""
MCP (Model Context Protocol) 实现

真正的 MCP 协议实现，支持：
- JSON-RPC 2.0 通信
- 工具调用（Tools）
- 资源访问（Resources）
- 提示模板（Prompts）
"""

from app.ai.mcp.protocol import (
    ToolDefinition,
    ToolCallRequest,
    ToolCallResult,
    Resource,
    ResourceContent,
    MCPMethod,
)
from app.ai.mcp.server import MCPServer, InProcessMCPServer, StdioMCPServer
from app.ai.mcp.client import MCPClient, MCPClientPool, MCP_CLIENT_POOL
from app.ai.mcp.tools_server import (
    CalculatorMCPServer,
    WeatherMCPServer,
    SearchMCPServer,
    create_all_mcp_servers,
)

__all__ = [
    # 协议类型
    "ToolDefinition",
    "ToolCallRequest",
    "ToolCallResult",
    "Resource",
    "ResourceContent",
    "MCPMethod",

    # 服务器
    "MCPServer",
    "InProcessMCPServer",
    "StdioMCPServer",

    # 客户端
    "MCPClient",
    "MCPClientPool",
    "MCP_CLIENT_POOL",

    # 工具服务器
    "CalculatorMCPServer",
    "WeatherMCPServer",
    "SearchMCPServer",
    "create_all_mcp_servers",
]

