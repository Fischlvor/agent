"""
MCP 工具适配器（真正的 MCP）

将 MCP 客户端的工具转换为 ADK FunctionTool
"""

import logging
from typing import List
from google.adk.tools import FunctionTool

from app.ai.mcp.client import MCPClient
from app.ai.mcp.tools_server import create_all_mcp_servers

LOGGER = logging.getLogger(__name__)


async def create_mcp_tools_for_adk(mcp_client: MCPClient) -> List[FunctionTool]:
    """
    从 MCP 客户端创建 ADK FunctionTool 列表

    Args:
        mcp_client: MCP 客户端实例

    Returns:
        ADK FunctionTool 列表
    """
    adk_tools = []

    # 获取所有工具
    all_tools = await mcp_client.list_all_tools()

    for server_name, tools in all_tools.items():
        for tool_def in tools:
            # 为每个 MCP 工具创建对应的 ADK FunctionTool
            adk_tool = create_adk_tool_from_mcp(
                mcp_client=mcp_client,
                server_name=server_name,
                tool_def=tool_def
            )
            adk_tools.append(adk_tool)

            LOGGER.info(f"Created ADK tool from MCP: {tool_def.name} (server: {server_name})")

    return adk_tools


def create_adk_tool_from_mcp(
    mcp_client: MCPClient,
    server_name: str,
    tool_def
) -> FunctionTool:
    """
    从 MCP 工具定义创建 ADK FunctionTool

    Args:
        mcp_client: MCP 客户端
        server_name: MCP 服务器名称
        tool_def: MCP 工具定义

    Returns:
        ADK FunctionTool
    """
    tool_name = tool_def.name
    tool_description = tool_def.description

    # 创建执行函数
    async def execute_mcp_tool(**kwargs):
        """
        执行 MCP 工具

        这个函数会被 ADK 调用
        """
        try:
            LOGGER.info(f"Executing MCP tool: {tool_name}")
            LOGGER.debug(f"Arguments: {kwargs}")

            # 通过 MCP 客户端调用工具
            result = await mcp_client.call_tool(
                tool_name=tool_name,
                arguments=kwargs,
                server_name=server_name
            )

            # 提取文本结果
            if result.isError:
                error_msg = result.content[0].get("text", "Unknown error")
                LOGGER.error(f"MCP tool error: {error_msg}")
                return f"错误: {error_msg}"

            # 返回结果文本
            result_text = result.content[0].get("text", "")
            LOGGER.info(f"MCP tool executed successfully: {tool_name}")

            return result_text

        except Exception as e:
            LOGGER.exception(f"Error executing MCP tool {tool_name}: {e}")
            return f"工具执行失败: {str(e)}"

    # 设置函数元数据（ADK 会读取）
    execute_mcp_tool.__name__ = tool_name
    execute_mcp_tool.__doc__ = _generate_docstring(tool_def)

    # 动态设置函数签名（从 inputSchema 提取参数）
    import inspect
    from typing import get_type_hints

    # 从 JSON Schema 生成参数
    from typing import Optional
    params = []
    input_schema = tool_def.inputSchema
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    for param_name, param_schema in properties.items():
        # 创建参数对象
        param_type = _json_schema_type_to_python(param_schema.get("type", "string"))

        # ✅ 如果参数是可选的，类型注解必须是 Optional[type]
        if param_name not in required:
            param_type = Optional[param_type]
            default = None
        else:
            default = inspect.Parameter.empty

        param = inspect.Parameter(
            name=param_name,
            kind=inspect.Parameter.KEYWORD_ONLY,
            default=default,
            annotation=param_type
        )
        params.append(param)

    # 设置新签名
    new_sig = inspect.Signature(parameters=params)
    execute_mcp_tool.__signature__ = new_sig

    # 创建 ADK FunctionTool
    return FunctionTool(func=execute_mcp_tool)


def _generate_docstring(tool_def) -> str:
    """
    从 MCP 工具定义生成 Python docstring

    Args:
        tool_def: MCP 工具定义

    Returns:
        docstring 字符串
    """
    lines = [tool_def.description, ""]

    # 添加参数说明
    input_schema = tool_def.inputSchema
    properties = input_schema.get("properties", {})
    required = input_schema.get("required", [])

    if properties:
        lines.append("Args:")
        for param_name, param_schema in properties.items():
            param_desc = param_schema.get("description", "")
            param_type = param_schema.get("type", "string")
            required_mark = " (必需)" if param_name in required else " (可选)"
            lines.append(f"    {param_name} ({param_type}){required_mark}: {param_desc}")

    return "\n".join(lines)


def _json_schema_type_to_python(json_type: str):
    """
    将 JSON Schema 类型转换为 Python 类型

    Args:
        json_type: JSON Schema 类型名称

    Returns:
        Python 类型
    """
    type_mapping = {
        "string": str,
        "number": float,
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
    }

    return type_mapping.get(json_type, str)


async def setup_mcp_tools_for_session(session_id: str) -> MCPClient:
    """
    为会话设置 MCP 工具

    Args:
        session_id: 会话 ID

    Returns:
        配置好的 MCP 客户端
    """
    from app.ai.mcp import MCP_CLIENT_POOL

    # 获取或创建客户端
    mcp_client = MCP_CLIENT_POOL.get_or_create_client(session_id)

    # 如果客户端还没有注册服务器，注册所有工具服务器
    if not mcp_client.servers:
        LOGGER.info(f"Setting up MCP servers for session: {session_id}")

        # 创建所有 MCP 服务器
        servers = await create_all_mcp_servers()

        # 注册到客户端
        for server_name, server in servers.items():
            await mcp_client.register_server(server_name, server)

        LOGGER.info(f"Registered {len(servers)} MCP servers for session {session_id}")

    return mcp_client

