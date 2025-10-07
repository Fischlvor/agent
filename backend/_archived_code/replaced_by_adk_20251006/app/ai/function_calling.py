"""函数调用处理模块。"""

import json
import logging
import re
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple, Union

from .tools.executor import EXECUTOR

LOGGER = logging.getLogger(__name__)


class FunctionCallParser:
    """函数调用解析器，用于解析AI模型输出中的函数调用"""

    def __init__(self):
        """初始化函数调用解析器"""
        # 函数调用的正则表达式模式
        self.patterns = [
            # 格式1: {{function_name(param1="value1", param2="value2")}}
            r"\{\{([a-zA-Z0-9_]+)\((.*?)\)\}\}",
            # 格式2: function_name(param1="value1", param2="value2")
            # 不匹配已经被{{}}包裹的函数调用
            r"(?<!\{\{)([a-zA-Z0-9_]+)\((.*?)\)(?!\}\})",
            # 格式3: {"name": "function_name", "arguments": {"param1": "value1"}}
            r'\{"name":\s*"([a-zA-Z0-9_]+)",\s*"arguments":\s*(\{.*?\})\}',
        ]

    def extract_function_calls(self, text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取函数调用

        Args:
            text: AI模型生成的文本

        Returns:
            函数调用列表，每个函数调用是一个字典，包含函数名和参数
        """
        function_calls = []
        matched_positions = set()  # 用于跟踪已匹配的位置

        # 尝试使用不同的模式匹配函数调用
        for pattern in self.patterns:
            for match in re.finditer(pattern, text):
                start, end = match.span()

                # 检查是否与已匹配的位置重叠
                overlap = False
                for pos_start, pos_end in matched_positions:
                    if start <= pos_end and end >= pos_start:
                        overlap = True
                        break

                if overlap:
                    continue

                # 记录匹配位置
                matched_positions.add((start, end))

                function_name, args_str = match.groups()

                try:
                    # 尝试解析参数
                    if args_str.strip().startswith("{"):
                        # JSON格式的参数
                        arguments = json.loads(args_str)
                    else:
                        # 键值对格式的参数
                        arguments = self._parse_key_value_args(args_str)

                    function_call = {
                        "function": {
                            "name": function_name,
                            "arguments": arguments
                        }
                    }

                    function_calls.append(function_call)

                except Exception as error:
                    LOGGER.warning("解析函数调用参数失败: %s, 函数: %s, 参数: %s",
                                   str(error), function_name, args_str)

        return function_calls

    def _parse_key_value_args(self, args_str: str) -> Dict[str, Any]:
        """
        解析键值对格式的参数字符串

        Args:
            args_str: 参数字符串，如 'param1="value1", param2=42'

        Returns:
            参数字典
        """
        arguments = {}

        if not args_str.strip():
            return arguments

        # 分割参数
        parts = []
        current_part = ""
        in_quotes = False
        quote_char = None

        for char in args_str:
            if char in ['"', "'"] and (not in_quotes or char == quote_char):
                in_quotes = not in_quotes
                quote_char = char if in_quotes else None
                current_part += char
            elif char == "," and not in_quotes:
                parts.append(current_part.strip())
                current_part = ""
            else:
                current_part += char

        if current_part.strip():
            parts.append(current_part.strip())

        # 解析每个参数
        for part in parts:
            if "=" in part:
                key, value = part.split("=", 1)
                key = key.strip()
                value = value.strip()

                # 去除引号
                if (value.startswith('"')
                        and value.endswith('"')) or (value.startswith("'")
                                                     and value.endswith("'")):
                    value = value[1:-1]
                # 尝试转换为数字或布尔值
                elif value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                else:
                    try:
                        if "." in value:
                            value = float(value)
                        else:
                            value = int(value)
                    except ValueError:
                        pass

                arguments[key] = value

        return arguments


class FunctionCallingHandler:
    """函数调用处理器，用于处理AI模型的函数调用"""

    def __init__(self, parser: Optional[FunctionCallParser] = None):
        """
        初始化函数调用处理器

        Args:
            parser: 函数调用解析器，如果为None则创建一个新的
        """
        self.parser = parser or FunctionCallParser()

    async def process_response(
        self,
        response: Union[str, Dict[str, Any]],
        available_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        处理AI模型的响应，提取并执行函数调用

        Args:
            response: AI模型的响应，可以是文本或包含工具调用的字典
            available_tools: 可用工具列表，如果为None则使用注册表中的所有工具

        Returns:
            元组 (处理后的响应文本, 函数调用结果列表)
        """
        # 提取函数调用
        function_calls = []
        response_text = ""

        if isinstance(response, str):
            # 如果响应是字符串，尝试从中提取函数调用
            response_text = response
            function_calls = self.parser.extract_function_calls(response)
        else:
            # 如果响应是字典，检查是否包含工具调用
            if "content" in response:
                response_text = response.get("content", "")

            if "tool_calls" in response:
                function_calls = response.get("tool_calls", [])

        # 如果没有函数调用，直接返回原始响应
        if not function_calls:
            return response_text, []

        # 执行函数调用
        results = []
        for function_call in function_calls:
            try:
                # 执行工具调用
                tool_name, result = await EXECUTOR.execute_tool_call(
                    function_call)

                # 构建函数调用结果
                call_result = {
                    "tool_name": tool_name,
                    "result": result,
                    "original_call": function_call,
                }

                results.append(call_result)

            except Exception as error:
                LOGGER.error("执行函数调用失败: %s", str(error))
                results.append({
                    "tool_name":
                    function_call.get("function", {}).get("name", "unknown"),
                    "error":
                    str(error),
                    "original_call":
                    function_call,
                })

        return response_text, results

    async def process_streaming_response(
        self,
        response_iterator: AsyncIterator[Dict[str, Any]],
        available_tools: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        处理AI模型的流式响应，提取并执行函数调用

        Args:
            response_iterator: AI模型的流式响应迭代器
            available_tools: 可用工具列表，如果为None则使用注册表中的所有工具

        Yields:
            处理后的响应块，包括原始内容和函数调用结果
        """
        buffer = ""

        async for chunk in response_iterator:
            # 检查是否包含工具调用
            if ("message" in chunk and "tool_calls" in chunk["message"]
                    and chunk["message"]["tool_calls"]):
                # 直接执行工具调用
                tool_calls = chunk["message"]["tool_calls"]

                # 执行工具调用
                results = await EXECUTOR.execute_tool_calls(tool_calls)

                # 产生包含工具调用结果的块
                yield {
                    "original_chunk": chunk,
                    "tool_results": results,
                }

            elif ("message" in chunk and "content" in chunk["message"]
                  and chunk["message"]["content"]):
                # 累积内容
                content = chunk["message"]["content"]
                buffer += content

                # 检查是否有函数调用
                function_calls = self.parser.extract_function_calls(buffer)

                if function_calls:
                    # 执行函数调用
                    results = await EXECUTOR.execute_tool_calls(function_calls)

                    # 清空缓冲区
                    buffer = ""

                    # 产生包含工具调用结果的块
                    yield {
                        "original_chunk": chunk,
                        "tool_results": results,
                    }
                else:
                    # 没有函数调用，直接产生原始块
                    yield {
                        "original_chunk": chunk,
                    }
            else:
                # 其他类型的块，直接产生
                yield {
                    "original_chunk": chunk,
                }


# 全局函数调用处理器实例
HANDLER = FunctionCallingHandler()
