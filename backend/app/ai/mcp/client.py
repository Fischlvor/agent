"""
MCP Client 实现

用于 AI Agent 调用 MCP 服务器
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

from app.ai.mcp.protocol import (
    JSONRPCRequest,
    MCPMethod,
    InitializeRequest,
    InitializeResult,
    ClientCapabilities,
    ToolDefinition,
    ToolCallRequest,
    ToolCallResult,
    ListToolsResult,
)

LOGGER = logging.getLogger(__name__)


class MCPClient:
    """
    MCP 客户端

    负责与 MCP 服务器通信，调用工具
    """

    def __init__(self, client_name: str = "ADK Agent", client_version: str = "1.0.0"):
        """
        初始化 MCP 客户端

        Args:
            client_name: 客户端名称
            client_version: 客户端版本
        """
        self.client_name = client_name
        self.client_version = client_version
        self.servers: Dict[str, Any] = {}  # server_name -> server instance
        self._request_id = 0

    def _next_request_id(self) -> int:
        """生成下一个请求 ID"""
        self._request_id += 1
        return self._request_id

    async def register_server(self, server_name: str, server: Any):
        """
        注册 MCP 服务器

        Args:
            server_name: 服务器名称（唯一标识）
            server: MCP 服务器实例
        """
        LOGGER.info(f"Registering MCP server: {server_name}")

        # 初始化服务器
        init_request = JSONRPCRequest(
            id=self._next_request_id(),
            method=MCPMethod.INITIALIZE,
            params=InitializeRequest(
                protocolVersion="2024-11-05",
                capabilities=ClientCapabilities().model_dump(exclude_none=True),
                clientInfo={
                    "name": self.client_name,
                    "version": self.client_version
                }
            ).model_dump()
        )

        response = await server.handle_request(init_request.model_dump())

        if "error" in response and response["error"]:
            raise RuntimeError(f"Failed to initialize server: {response['error']}")

        result = InitializeResult(**response["result"])
        LOGGER.info(f"Server initialized: {result.serverInfo}")

        self.servers[server_name] = server

    async def list_all_tools(self) -> Dict[str, List[ToolDefinition]]:
        """
        列出所有服务器的工具

        Returns:
            {server_name: [tools...]}
        """
        all_tools = {}

        for server_name, server in self.servers.items():
            request = JSONRPCRequest(
                id=self._next_request_id(),
                method=MCPMethod.TOOLS_LIST,
                params={}
            )

            response = await server.handle_request(request.model_dump())

            if "error" in response and response["error"]:
                LOGGER.error(f"Error listing tools from {server_name}: {response['error']}")
                continue

            result = ListToolsResult(**response["result"])
            all_tools[server_name] = result.tools

            LOGGER.info(f"Server '{server_name}' provides {len(result.tools)} tools")

        return all_tools

    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        server_name: Optional[str] = None
    ) -> ToolCallResult:
        """
        调用工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数
            server_name: 服务器名称（如果不指定，会自动查找）

        Returns:
            工具执行结果
        """
        # 如果没有指定服务器，查找哪个服务器提供这个工具
        if not server_name:
            server_name = await self._find_tool_server(tool_name)
            if not server_name:
                raise ValueError(f"Tool '{tool_name}' not found in any server")

        server = self.servers.get(server_name)
        if not server:
            raise ValueError(f"Server '{server_name}' not registered")

        LOGGER.info(f"Calling tool '{tool_name}' on server '{server_name}'")
        LOGGER.debug(f"Arguments: {arguments}")

        # 构造请求
        request = JSONRPCRequest(
            id=self._next_request_id(),
            method=MCPMethod.TOOLS_CALL,
            params=ToolCallRequest(
                name=tool_name,
                arguments=arguments
            ).model_dump()
        )

        # 发送请求
        response = await server.handle_request(request.model_dump())

        if "error" in response and response["error"]:
            error = response["error"]
            raise RuntimeError(f"Tool call failed: {error.get('message', error)}")

        result = ToolCallResult(**response["result"])

        LOGGER.info(f"Tool '{tool_name}' executed successfully")

        return result

    async def _find_tool_server(self, tool_name: str) -> Optional[str]:
        """
        查找提供指定工具的服务器

        Args:
            tool_name: 工具名称

        Returns:
            服务器名称，如果找不到返回 None
        """
        all_tools = await self.list_all_tools()

        for server_name, tools in all_tools.items():
            for tool in tools:
                if tool.name == tool_name:
                    return server_name

        return None

    async def get_tool_schema(self, tool_name: str) -> Optional[ToolDefinition]:
        """
        获取工具的 schema

        Args:
            tool_name: 工具名称

        Returns:
            工具定义，如果找不到返回 None
        """
        all_tools = await self.list_all_tools()

        for server_name, tools in all_tools.items():
            for tool in tools:
                if tool.name == tool_name:
                    return tool

        return None


class MCPClientPool:
    """
    MCP 客户端池

    管理多个 MCP 客户端（用于不同的会话）
    """

    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}

    def get_or_create_client(self, session_id: str) -> MCPClient:
        """
        获取或创建客户端

        Args:
            session_id: 会话 ID

        Returns:
            MCP 客户端实例
        """
        if session_id not in self.clients:
            self.clients[session_id] = MCPClient()

        return self.clients[session_id]

    def remove_client(self, session_id: str):
        """删除客户端"""
        if session_id in self.clients:
            del self.clients[session_id]


# ============ 全局客户端池 ============

# 用于整个应用的 MCP 客户端池
MCP_CLIENT_POOL = MCPClientPool()

