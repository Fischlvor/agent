"""工具调用网关模块。

提供统一的工具调用入口，简化工具调用流程。
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .registry import REGISTRY

LOGGER = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """工具执行错误"""


class ToolGateway:
    """工具调用网关，提供统一的工具调用入口"""

    def __init__(self, registry=None):
        """
        初始化工具网关

        Args:
            registry: 工具注册表，默认使用全局注册表
        """
        self.registry = registry or REGISTRY

    async def call_tool(
        self,
        tool_name: str,
        **kwargs: Any
    ) -> Any:
        """
        调用指定工具

        Args:
            tool_name: 工具名称
            **kwargs: 工具参数

        Returns:
            工具执行结果

        Raises:
            ToolExecutionError: 工具执行错误
        """
        try:
            # 获取工具实例
            tool_instance = self.registry.get_instance(tool_name)
            if not tool_instance:
                raise ToolExecutionError(f"工具 '{tool_name}' 未注册")

            # 记录调用信息
            LOGGER.info(
                "调用工具 '%s'，参数: %s",
                tool_name,
                json.dumps(kwargs, ensure_ascii=False, default=str)
            )

            # 执行工具
            result = await tool_instance.execute(**kwargs)

            # 记录执行结果
            LOGGER.info(
                "工具 '%s' 执行成功，结果: %s",
                tool_name,
                json.dumps(result, ensure_ascii=False, default=str)
            )

            return result

        except Exception as e:
            error_msg = f"工具 '{tool_name}' 执行失败: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            raise ToolExecutionError(error_msg) from e

    async def call_tools(
        self,
        tool_calls: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        批量调用多个工具

        Args:
            tool_calls: 工具调用列表，每个元素包含tool_name和arguments

        Returns:
            工具名称到执行结果的映射
        """
        results = {}

        for tool_call in tool_calls:
            tool_name = tool_call.get("tool_name")
            arguments = tool_call.get("arguments", {})

            if not tool_name:
                LOGGER.warning("工具调用缺少tool_name: %s", tool_call)
                continue

            try:
                result = await self.call_tool(tool_name, **arguments)
                results[tool_name] = result
            except ToolExecutionError as e:
                LOGGER.error("工具调用失败: %s", str(e))
                results[tool_name] = {"error": str(e)}

        return results

    async def call_tool_from_function_call(
        self,
        function_call: Dict[str, Any]
    ) -> Any:
        """
        从标准函数调用格式调用工具

        Args:
            function_call: 标准函数调用格式，如：
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": {"location": "Beijing"}
                    }
                }

        Returns:
            工具执行结果
        """
        function_info = function_call.get("function", {})
        tool_name = function_info.get("name")
        arguments = function_info.get("arguments", {})

        # 如果arguments是字符串，尝试解析为JSON
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError as e:
                raise ToolExecutionError(f"无法解析工具参数: {arguments}") from e

        return await self.call_tool(tool_name, **arguments)

    def get_available_tools(self) -> List[str]:
        """
        获取所有可用工具名称

        Returns:
            工具名称列表
        """
        return list(self.registry.get_all_tools().keys())

    def get_tool_schema(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        获取指定工具的Schema

        Args:
            tool_name: 工具名称

        Returns:
            工具Schema，如果工具不存在则返回None
        """
        tool_class = self.registry.get_tool(tool_name)
        if tool_class:
            return tool_class.get_schema()
        return None

    def get_all_tool_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的Schema

        Returns:
            工具Schema列表
        """
        return self.registry.get_all_schemas()

    def is_tool_available(self, tool_name: str) -> bool:
        """
        检查工具是否可用

        Args:
            tool_name: 工具名称

        Returns:
            工具是否可用
        """
        return tool_name in self.registry.get_all_tools()


# 全局工具网关实例
GATEWAY = ToolGateway()


# 便捷函数
async def call_tool(tool_name: str, **kwargs: Any) -> Any:
    """
    便捷函数：调用指定工具

    Args:
        tool_name: 工具名称
        **kwargs: 工具参数

    Returns:
        工具执行结果
    """
    return await GATEWAY.call_tool(tool_name, **kwargs)


async def call_tools(tool_calls: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    便捷函数：批量调用多个工具

    Args:
        tool_calls: 工具调用列表

    Returns:
        工具名称到执行结果的映射
    """
    return await GATEWAY.call_tools(tool_calls)


def get_available_tools() -> List[str]:
    """
    便捷函数：获取所有可用工具名称

    Returns:
        工具名称列表
    """
    return GATEWAY.get_available_tools()


def get_tool_schema(tool_name: str) -> Optional[Dict[str, Any]]:
    """
    便捷函数：获取指定工具的Schema

    Args:
        tool_name: 工具名称

    Returns:
        工具Schema
    """
    return GATEWAY.get_tool_schema(tool_name)
