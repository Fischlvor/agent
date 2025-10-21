"""
工具 MCP 服务器实现

将现有工具（计算器、搜索、天气）包装为 MCP 服务器
"""

import logging
from typing import Dict, Any, List

from app.ai.mcp.server import InProcessMCPServer
from app.ai.mcp.protocol import (
    ToolDefinition,
    ToolCallResult,
)
from app.ai.tools.general.calculator import CalculatorTool
from app.ai.tools.general.search import SearchTool
from app.ai.tools.general.weather import WeatherTool
from app.ai.tools.general.knowledge_search import KnowledgeSearchTool

LOGGER = logging.getLogger(__name__)


class CalculatorMCPServer(InProcessMCPServer):
    """计算器 MCP 服务器"""

    def __init__(self):
        super().__init__(name="calculator-server", version="1.0.0")
        self.calculator = CalculatorTool()

    async def get_tools(self) -> List[ToolDefinition]:
        """返回计算器工具定义（使用 BaseTool 的参数描述）"""
        # 从 CalculatorTool 获取参数定义
        params = CalculatorTool.get_parameters()

        # 构建 inputSchema
        properties = {}
        required = []

        for param_name, param_info in params.items():
            properties[param_name] = {
                "type": "string",
                "description": param_info.description
            }

            if param_info.required:
                required.append(param_name)

        return [
            ToolDefinition(
                name="calculate",
                description=CalculatorTool.get_description(),
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            )
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        """执行计算器工具"""
        if name != "calculate":
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }],
                isError=True
            )

        try:
            expression = arguments.get("expression")
            if not expression:
                raise ValueError("Missing 'expression' parameter")

            # 调用计算器工具
            result = await self.calculator.execute(expression=expression)

            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": str(result)
                }],
                isError=False
            )

        except Exception as e:
            LOGGER.error(f"Calculator error: {e}")
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"计算错误: {str(e)}"
                }],
                isError=True
            )


class WeatherMCPServer(InProcessMCPServer):
    """天气查询 MCP 服务器"""

    def __init__(self):
        super().__init__(name="weather-server", version="1.0.0")
        self.weather = WeatherTool()

    async def get_tools(self) -> List[ToolDefinition]:
        """返回天气工具定义（使用 BaseTool 的参数描述）"""
        # 从 WeatherTool 获取参数定义
        params = WeatherTool.get_parameters()

        # 构建 inputSchema（将 location 映射为 city）
        properties = {}
        required = []

        for param_name, param_info in params.items():
            # 将 WeatherTool 的 location 参数映射为 MCP 的 city 参数
            mcp_param_name = "city" if param_name == "location" else param_name

            properties[mcp_param_name] = {
                "type": "string",
                "description": param_info.description
            }

            if param_info.required:
                required.append(mcp_param_name)

        return [
            ToolDefinition(
                name="get_weather",
                description=WeatherTool.get_description(),
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            )
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        """执行天气查询工具"""
        if name != "get_weather":
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }],
                isError=True
            )

        try:
            city = arguments.get("city")
            unit = arguments.get("unit", "celsius")

            if not city:
                raise ValueError("Missing 'city' parameter")

            # 调用天气工具（注意：WeatherTool.execute 参数是 location，不是 city）
            result = await self.weather.execute(location=city, unit=unit)

            # 格式化输出
            import json
            result_text = json.dumps(result, ensure_ascii=False, indent=2)

            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": result_text
                }],
                isError=False
            )

        except Exception as e:
            LOGGER.error(f"Weather query error: {e}")
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"天气查询错误: {str(e)}"
                }],
                isError=True
            )


class SearchMCPServer(InProcessMCPServer):
    """搜索 MCP 服务器"""

    def __init__(self):
        super().__init__(name="search-server", version="1.0.0")
        self.search = SearchTool()

    async def get_tools(self) -> List[ToolDefinition]:
        """返回搜索工具定义（使用 BaseTool 的参数描述）"""
        # 从 SearchTool 获取参数定义
        params = SearchTool.get_parameters()

        # 构建 inputSchema
        properties = {}
        required = []

        for param_name, param_info in params.items():
            properties[param_name] = {
                "type": "string",
                "description": param_info.description
            }

            if param_info.required:
                required.append(param_name)

        return [
            ToolDefinition(
                name="search_web",
                description=SearchTool.get_description(),
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            )
        ]

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        """执行搜索工具"""
        if name != "search_web":
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }],
                isError=True
            )

        try:
            query = arguments.get("query")
            if not query:
                raise ValueError("Missing 'query' parameter")

            # 调用搜索工具
            result = await self.search.execute(query=query)

            # 格式化输出
            import json
            result_text = json.dumps(result, ensure_ascii=False, indent=2)

            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": result_text
                }],
                isError=False
            )

        except Exception as e:
            LOGGER.error(f"Search error: {e}")
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"搜索错误: {str(e)}"
                }],
                isError=True
            )


class KnowledgeSearchMCPServer(InProcessMCPServer):
    """知识库检索 MCP 服务器"""

    def __init__(self):
        super().__init__(name="knowledge-search-server", version="1.0.0")
        self.knowledge_search = KnowledgeSearchTool()

    async def get_tools(self) -> List[ToolDefinition]:
        """返回知识库检索工具定义（动态获取知识库列表）"""
        # 从 KnowledgeSearchTool 获取参数定义
        params = KnowledgeSearchTool.get_parameters()

        # 构建 inputSchema
        properties = {}
        required = []

        for param_name, param_info in params.items():
            prop_type = "string"
            if param_info.type in ["int", "integer"]:
                prop_type = "integer"
            elif param_info.type in ["float", "number"]:
                prop_type = "number"

            properties[param_name] = {
                "type": prop_type,
                "description": param_info.description
            }

            if param_info.required:
                required.append(param_name)

        # 动态生成工具描述（包含可用知识库列表）
        description = await self._build_tool_description()

        return [
            ToolDefinition(
                name="search_knowledge_base",
                description=description,
                inputSchema={
                    "type": "object",
                    "properties": properties,
                    "required": required
                }
            )
        ]

    async def _build_tool_description(self) -> str:
        """动态构建工具描述，包含可用知识库列表"""
        base_description = KnowledgeSearchTool.get_description()

        # 尝试获取知识库列表
        try:
            from app.ai.context import get_current_db_session
            db = get_current_db_session()

            if db is not None:
                from app.models.rag import KnowledgeBase

                # 查询所有知识库
                kbs = db.query(KnowledgeBase).order_by(KnowledgeBase.id).all()

                if kbs:
                    kb_list = "\n\nAvailable knowledge bases:\n"
                    for kb in kbs:
                        kb_desc = kb.description or "No description"
                        doc_count = kb.doc_count or 0
                        kb_list += f"- kb_id={kb.id}: {kb.name} ({kb_desc}) - {doc_count} documents\n"

                    return base_description + kb_list

        except Exception as e:
            LOGGER.warning(f"Failed to load knowledge base list: {e}")

        # 如果无法获取知识库列表，返回基础描述
        return base_description + "\n\nNote: Specify kb_id parameter to search a specific knowledge base."

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> ToolCallResult:
        """执行知识库检索工具"""
        if name != "search_knowledge_base":
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"Unknown tool: {name}"
                }],
                isError=True
            )

        try:
            query = arguments.get("query")
            kb_id = arguments.get("kb_id")
            top_k = arguments.get("top_k", 5)

            if not query:
                raise ValueError("Missing 'query' parameter")
            if not kb_id:
                raise ValueError("Missing 'kb_id' parameter")

            # 调用知识库检索工具
            result = await self.knowledge_search.execute(
                query=query,
                kb_id=int(kb_id),
                top_k=int(top_k)
            )

            # 格式化输出
            import json
            result_text = json.dumps(result, ensure_ascii=False, indent=2)

            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": result_text
                }],
                isError=False
            )

        except Exception as e:
            LOGGER.error(f"Knowledge search error: {e}")
            return ToolCallResult(
                content=[{
                    "type": "text",
                    "text": f"知识库检索错误: {str(e)}"
                }],
                isError=True
            )


# ============ 工厂函数 ============

async def create_all_mcp_servers() -> Dict[str, InProcessMCPServer]:
    """
    创建所有工具 MCP 服务器

    Returns:
        {server_name: server_instance}
    """
    servers = {
        "calculator": CalculatorMCPServer(),
        "weather": WeatherMCPServer(),
        "search": SearchMCPServer(),
        "knowledge_search": KnowledgeSearchMCPServer(),  # ✅ RAG 知识库检索工具
    }

    LOGGER.info(f"Created {len(servers)} MCP servers")

    return servers

