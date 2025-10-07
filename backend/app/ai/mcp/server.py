"""
MCP Server 基础实现

提供标准的 MCP 服务器基类，工具服务器可以继承此类
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod

from app.ai.mcp.protocol import (
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    MCPMethod,
    InitializeRequest,
    InitializeResult,
    ServerCapabilities,
    ToolDefinition,
    ToolCallRequest,
    ToolCallResult,
    ListToolsResult,
    Resource,
    ResourceContent,
    ListResourcesResult,
)

LOGGER = logging.getLogger(__name__)


class MCPServer(ABC):
    """
    MCP 服务器基类

    子类需要实现：
    - get_tools(): 返回工具列表
    - call_tool(): 执行工具调用
    - get_resources(): 返回资源列表（可选）
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        """
        初始化 MCP 服务器

        Args:
            name: 服务器名称
            version: 服务器版本
        """
        self.name = name
        self.version = version
        self.initialized = False
        self._request_handlers: Dict[str, Callable] = {}

        # 注册标准处理器
        self._register_handlers()

    def _register_handlers(self):
        """注册 JSON-RPC 请求处理器"""
        self._request_handlers = {
            MCPMethod.INITIALIZE: self._handle_initialize,
            MCPMethod.TOOLS_LIST: self._handle_tools_list,
            MCPMethod.TOOLS_CALL: self._handle_tools_call,
            MCPMethod.RESOURCES_LIST: self._handle_resources_list,
            MCPMethod.RESOURCES_READ: self._handle_resources_read,
        }

    async def handle_request(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理 JSON-RPC 请求

        Args:
            request_data: JSON-RPC 请求数据

        Returns:
            JSON-RPC 响应数据
        """
        try:
            request = JSONRPCRequest(**request_data)

            # 查找处理器
            handler = self._request_handlers.get(request.method)
            if not handler:
                return self._create_error_response(
                    request.id,
                    -32601,
                    f"Method not found: {request.method}"
                )

            # 执行处理器
            result = await handler(request)

            return JSONRPCResponse(
                id=request.id,
                result=result
            ).model_dump()

        except Exception as e:
            LOGGER.exception(f"Error handling request: {e}")
            return self._create_error_response(
                request_data.get("id"),
                -32603,
                str(e)
            )

    def _create_error_response(
        self,
        request_id: Optional[Any],
        code: int,
        message: str
    ) -> Dict[str, Any]:
        """创建错误响应"""
        return JSONRPCResponse(
            id=request_id,
            error=JSONRPCError(
                code=code,
                message=message
            ).model_dump()
        ).model_dump()

    async def _handle_initialize(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """处理初始化请求"""
        init_request = InitializeRequest(**request.params)

        LOGGER.info(f"Initializing MCP server: {self.name}")
        LOGGER.info(f"Client: {init_request.clientInfo}")

        self.initialized = True

        # 返回服务器信息和能力
        result = InitializeResult(
            protocolVersion="2024-11-05",
            capabilities=ServerCapabilities(
                tools={} if self.supports_tools() else None,
                resources={} if self.supports_resources() else None,
            ).model_dump(exclude_none=True),
            serverInfo={
                "name": self.name,
                "version": self.version
            }
        )

        return result.model_dump()

    async def _handle_tools_list(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """处理列出工具请求"""
        if not self.initialized:
            raise RuntimeError("Server not initialized")

        tools = await self.get_tools()

        result = ListToolsResult(tools=tools)
        return result.model_dump()

    async def _handle_tools_call(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """处理工具调用请求"""
        if not self.initialized:
            raise RuntimeError("Server not initialized")

        tool_request = ToolCallRequest(**request.params)

        LOGGER.info(f"Calling tool: {tool_request.name}")
        LOGGER.debug(f"Arguments: {tool_request.arguments}")

        # 执行工具
        result = await self.call_tool(
            tool_request.name,
            tool_request.arguments
        )

        return result.model_dump()

    async def _handle_resources_list(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """处理列出资源请求"""
        if not self.initialized:
            raise RuntimeError("Server not initialized")

        resources = await self.get_resources()

        result = ListResourcesResult(resources=resources)
        return result.model_dump()

    async def _handle_resources_read(self, request: JSONRPCRequest) -> Dict[str, Any]:
        """处理读取资源请求"""
        if not self.initialized:
            raise RuntimeError("Server not initialized")

        uri = request.params.get("uri")
        if not uri:
            raise ValueError("Missing 'uri' parameter")

        content = await self.read_resource(uri)
        return {"contents": [content.model_dump()]}

    # ============ 子类需要实现的方法 ============

    @abstractmethod
    async def get_tools(self) -> List[ToolDefinition]:
        """
        返回此服务器提供的工具列表

        Returns:
            工具定义列表
        """
        pass

    @abstractmethod
    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        """
        执行工具调用

        Args:
            name: 工具名称
            arguments: 工具参数

        Returns:
            工具执行结果
        """
        pass

    def supports_tools(self) -> bool:
        """是否支持工具"""
        return True

    def supports_resources(self) -> bool:
        """是否支持资源"""
        return False

    async def get_resources(self) -> List[Resource]:
        """
        返回此服务器提供的资源列表

        Returns:
            资源列表
        """
        return []

    async def read_resource(self, uri: str) -> ResourceContent:
        """
        读取资源内容

        Args:
            uri: 资源 URI

        Returns:
            资源内容
        """
        raise NotImplementedError("This server does not support resources")


class StdioMCPServer(MCPServer):
    """
    基于标准输入/输出的 MCP 服务器

    用于进程间通信
    """

    async def run(self):
        """运行服务器（从 stdin 读取，向 stdout 写入）"""
        import sys

        LOGGER.info(f"Starting MCP server: {self.name}")

        try:
            while True:
                # 读取一行 JSON-RPC 请求
                line = sys.stdin.readline()
                if not line:
                    break

                try:
                    request_data = json.loads(line)
                    response_data = await self.handle_request(request_data)

                    # 写入响应
                    sys.stdout.write(json.dumps(response_data) + "\n")
                    sys.stdout.flush()

                except json.JSONDecodeError as e:
                    LOGGER.error(f"Invalid JSON: {e}")

        except KeyboardInterrupt:
            LOGGER.info("Server stopped by user")
        except Exception as e:
            LOGGER.exception(f"Server error: {e}")


class InProcessMCPServer(MCPServer):
    """
    进程内 MCP 服务器

    用于同一进程内的直接调用（不需要网络或 stdio）
    """

    async def call_directly(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        直接调用方法（跳过 JSON-RPC 序列化）

        Args:
            method: 方法名
            params: 参数

        Returns:
            响应结果
        """
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {}
        }

        response = await self.handle_request(request_data)

        if "error" in response and response["error"]:
            raise RuntimeError(f"MCP Error: {response['error']}")

        return response.get("result")

