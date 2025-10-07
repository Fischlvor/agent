"""工具执行器模块。"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Tuple

from .base import BaseTool
from .registry import REGISTRY

LOGGER = logging.getLogger(__name__)


class ToolExecutionError(Exception):
    """工具执行错误"""

    pass


class ToolExecutor:
    """工具执行器，负责安全地执行工具调用"""

    def __init__(
        self,
        timeout: float = 10.0,
        max_retries: int = 1,
        registry=REGISTRY,
    ):
        """
        初始化工具执行器

        Args:
            timeout: 工具执行超时时间（秒）
            max_retries: 最大重试次数
            registry: 工具注册表
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.registry = registry

    async def execute_tool_call(
        self,
        tool_call: Dict[str, Any],
    ) -> Tuple[str, Any]:
        """
        执行工具调用

        Args:
            tool_call: 工具调用信息，格式如：
                {
                    "function": {
                        "name": "get_weather",
                        "arguments": {
                            "location": "Beijing",
                            "unit": "celsius"
                        }
                    }
                }

        Returns:
            元组 (工具名称, 执行结果)

        Raises:
            ToolExecutionError: 工具执行错误
        """
        try:
            function_info = tool_call.get("function", {})
            tool_name = function_info.get("name")
            arguments_str = function_info.get("arguments", {})

            # 解析参数
            if isinstance(arguments_str, str):
                try:
                    arguments = json.loads(arguments_str)
                except json.JSONDecodeError:
                    raise ToolExecutionError(f"无法解析工具参数: {arguments_str}")
            else:
                arguments = arguments_str

            LOGGER.info(
                "执行工具 '%s' 参数: %s", tool_name, json.dumps(arguments, ensure_ascii=False)
            )

            # 获取工具实例
            tool_instance = self.registry.get_instance(tool_name)
            if not tool_instance:
                raise ToolExecutionError(f"工具 '{tool_name}' 未注册")

            # 执行工具，带超时和重试
            result = await self._execute_with_timeout_and_retry(
                tool_instance, arguments)

            # 格式化结果
            if isinstance(result, (dict, list)):
                result_str = json.dumps(result, ensure_ascii=False)
            else:
                result_str = str(result)

            LOGGER.info("工具 '%s' 执行结果: %s", tool_name, result_str)

            return tool_name, result

        except Exception as e:
            error_msg = f"工具执行错误: {str(e)}"
            LOGGER.error(error_msg, exc_info=True)
            raise ToolExecutionError(error_msg)

    async def execute_tool_calls(
        self,
        tool_calls: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        执行多个工具调用

        Args:
            tool_calls: 工具调用列表

        Returns:
            工具名称到执行结果的映射
        """
        results = {}

        for tool_call in tool_calls:
            try:
                tool_name, result = await self.execute_tool_call(tool_call)
                results[tool_name] = result
            except ToolExecutionError as e:
                LOGGER.error("工具执行错误: %s", str(e))
                results[tool_call.get("function",
                                      {}).get("name",
                                              "unknown")] = (f"错误: {str(e)}")

        return results

    async def _execute_with_timeout_and_retry(
        self,
        tool: BaseTool,
        arguments: Dict[str, Any],
    ) -> Any:
        """
        带超时和重试的工具执行

        Args:
            tool: 工具实例
            arguments: 工具参数

        Returns:
            工具执行结果

        Raises:
            ToolExecutionError: 工具执行错误
        """
        last_error = None

        for attempt in range(self.max_retries + 1):
            if attempt > 0:
                LOGGER.info(
                    "重试执行工具 '%s' (尝试 %s/%s)", tool.get_name(), attempt, self.max_retries
                )
                # 重试前等待
                await asyncio.sleep(0.5 * attempt)

            try:
                # 使用asyncio.wait_for实现超时控制
                start_time = time.time()
                result = await asyncio.wait_for(
                    tool.execute(**arguments),
                    timeout=self.timeout,
                )
                execution_time = time.time() - start_time
                LOGGER.debug(
                    "工具 '%s' 执行耗时: %.3f秒", tool.get_name(), execution_time)

                return result

            except asyncio.TimeoutError:
                last_error = ToolExecutionError(f"工具执行超时 (>{self.timeout}秒)")
            except Exception as e:
                last_error = ToolExecutionError(f"工具执行异常: {str(e)}")

        # 所有重试都失败
        if last_error:
            raise last_error
        else:
            raise ToolExecutionError("工具执行失败，原因未知")


# 全局工具执行器实例
EXECUTOR = ToolExecutor()
