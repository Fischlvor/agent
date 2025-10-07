"""Agent服务层，处理多轮工具调用"""

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from .clients.base import BaseAIClient, Message
from .tools.registry import REGISTRY
from .tools.gateway import GATEWAY

LOGGER = logging.getLogger(__name__)


class AgentService:
    """Agent服务，处理多轮工具调用"""

    def __init__(
            self,
            client: BaseAIClient,
            max_iterations: int = 50,
            debug: bool = False,
    ):
        """
        初始化Agent服务

        Args:
            client: AI客户端
            max_iterations: 最大迭代次数
            debug: 是否启用调试模式
        """
        self.client = client
        self.max_iterations = max_iterations
        self.debug = debug

    async def run(
            self,
            messages: List[Message],
            system_prompt: Optional[str] = None,
            tools: Optional[List[Dict[str, Any]]] = None,
            stop_on_first_tool: bool = False,
    ) -> Tuple[List[Message], List[Dict[str, Any]]]:
        """
        运行Agent，处理多轮工具调用

        Args:
            messages: 对话历史
            system_prompt: 系统提示
            tools: 可用工具列表，如果为None则使用注册表中的所有工具
            stop_on_first_tool: 是否在第一次工具调用后停止

        Returns:
            元组 (更新后的对话历史, 工具调用结果列表)
        """
        if tools is None:
            tools = REGISTRY.get_all_schemas()

        current_messages = messages.copy()
        all_tool_results = []

        for iteration in range(self.max_iterations):
            if self.debug:
                LOGGER.info("Agent迭代 %s/%s", iteration+1, self.max_iterations)
                LOGGER.info("当前消息: %s",
                            json.dumps(current_messages, ensure_ascii=False))

            # 调用模型获取响应
            # 客户端职责：仅与API通信，返回原始响应
            response = await self.client.chat(
                messages=current_messages,
                system_prompt=system_prompt,
                tools=tools,
                stream=False,
            )

            # User added print(response) here
            print(response)
            if self.debug:
                LOGGER.info("模型响应: %s",
                            json.dumps(response, ensure_ascii=False))

            # Agent职责：判断是否需要使用工具
            if "tool_calls" not in response or not response["tool_calls"]:
                # 没有工具调用，添加助手消息并返回
                current_messages.append({
                    "role": "assistant",
                    "content": response.get("content", "")
                })
                return current_messages, all_tool_results

            # 处理工具调用
            assistant_message = {
                "role": "assistant",
                "content": response.get("content", ""),
                "tool_calls": response["tool_calls"],
            }
            current_messages.append(assistant_message)

            # 执行工具调用
            iteration_tool_results = []
            for tool_call in response["tool_calls"]:
                # 执行工具调用
                tool_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]

                if self.debug:
                    LOGGER.info(
                        "执行工具 %s: %s", tool_name, json.dumps(arguments, ensure_ascii=False)
                    )

                try:
                    # 使用工具网关调用工具
                    result = await GATEWAY.call_tool(tool_name, **arguments)

                    # 构建工具响应消息
                    tool_message = {
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call.get("id", ""),
                    }
                    current_messages.append(tool_message)

                    # 保存工具调用结果
                    tool_result = {
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }
                    iteration_tool_results.append(tool_result)
                    all_tool_results.append(tool_result)

                    if self.debug:
                        LOGGER.info(
                            "工具 %s 执行结果: %s", tool_name, json.dumps(result, ensure_ascii=False)
                        )
                except Exception as tool_error:
                    error_message = f"工具 '{tool_name}' 执行失败: {str(tool_error)}"
                    LOGGER.error(error_message)

                    # 构建工具错误消息
                    tool_message = {
                        "role": "tool",
                        "content": f"错误: {error_message}",
                        "tool_call_id": tool_call.get("id", ""),
                    }
                    current_messages.append(tool_message)

            if stop_on_first_tool or not iteration_tool_results:
                # 如果设置了在第一次工具调用后停止，或者没有成功执行任何工具调用，则停止迭代
                return current_messages, all_tool_results

        # 达到最大迭代次数
        LOGGER.warning("达到最大迭代次数 %s", self.max_iterations)
        return current_messages, all_tool_results

    async def run_streaming(
            self,
            messages: List[Message],
            system_prompt: Optional[str] = None,
            tools: Optional[List[Dict[str, Any]]] = None,
            stop_on_first_tool: bool = False,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        运行Agent，处理多轮工具调用，支持流式输出

        Args:
            messages: 对话历史
            system_prompt: 系统提示
            tools: 可用工具列表，如果为None则使用注册表中的所有工具
            stop_on_first_tool: 是否在第一次工具调用后停止

        Yields:
            处理后的响应块，包括原始内容和函数调用结果
        """
        import asyncio  # pylint: disable=import-outside-toplevel

        if tools is None:
            tools = REGISTRY.get_all_schemas()

        current_messages = messages.copy()

        for iteration in range(self.max_iterations):
            if self.debug:
                LOGGER.info("Agent流式迭代 %s/%s", iteration+1, self.max_iterations)

            # 调用模型获取流式响应
            # 客户端职责：仅流式返回API数据块
            response_stream = await self.client.chat(
                messages=current_messages,
                system_prompt=system_prompt,
                tools=tools,
                stream=True,
            )

            # Agent职责：处理流式数据，判断是否有工具调用
            buffer = ""
            tool_calls = []

            async for chunk in response_stream:
                # Ollama 流式响应格式（实测结果）：
                # - 内容 chunks: {"message": {"role": "assistant", "content": "部分内容"}, "done": false}
                # - tool_calls chunk: {"message": {"role": "assistant", "content": "", "tool_calls": [...]}, "done": false}
                # - 最后 chunk: {"message": {"role": "assistant", "content": ""}, "done": true}
                # 注意：tool_calls 出现在倒数第二个 chunk（done: false），不是最后一个！

                if "message" in chunk:
                    message = chunk["message"]

                    # 处理内容（流式输出）
                    if "content" in message and message["content"] is not None:
                        content = message["content"]
                        # 将内容添加到缓冲区
                        buffer += content
                        # 无论是什么内容，都直接流式输出
                        yield {
                            "type": "content",
                            "role": message.get("role", "assistant"),  # 添加角色信息
                            "content": content
                        }
                        # 确保立即刷新输出
                        await asyncio.sleep(0)

                    # 检查是否有工具调用（在倒数第二个 chunk 中出现）
                    if "tool_calls" in message and message["tool_calls"]:
                        # 使用 extend 累积所有 tool_calls，避免覆盖
                        new_tool_calls = message["tool_calls"]
                        tool_calls.extend(new_tool_calls)
                        yield {
                            "type": "tool_calls",
                            "role": message.get("role", "assistant"),  # 添加角色信息
                            "tool_calls": new_tool_calls  # 只返回本次新增的
                        }

            # 如果没有工具调用，结束迭代
            if not tool_calls:
                # 添加助手消息
                current_messages.append({
                    "role": "assistant",
                    "content": buffer
                })
                # 不要直接return，而是使用break跳出循环
                break

            # 添加助手消息，包含工具调用
            assistant_message = {
                "role": "assistant",
                "content": buffer,
                "tool_calls": tool_calls,
            }
            current_messages.append(assistant_message)

            # 执行工具调用
            for tool_call in tool_calls:
                # 执行工具调用
                tool_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]

                if self.debug:
                    LOGGER.info(
                        "执行工具 %s: %s", tool_name, json.dumps(arguments, ensure_ascii=False)
                    )

                try:
                    # 使用工具网关调用工具
                    result = await GATEWAY.call_tool(tool_name, **arguments)

                    # 构建工具响应消息
                    tool_message = {
                        "role": "tool",
                        "content": json.dumps(result, ensure_ascii=False),
                        "tool_call_id": tool_call.get("id", ""),
                    }
                    current_messages.append(tool_message)

                    yield {
                        "type": "tool_result",
                        "role": "tool",  # 添加角色信息
                        "tool_name": tool_name,
                        "arguments": arguments,
                        "result": result,
                    }

                    if self.debug:
                        LOGGER.info(
                            "工具 %s 执行结果: %s", tool_name, json.dumps(result, ensure_ascii=False)
                        )
                except Exception as tool_error:
                    error_message = f"工具 '{tool_name}' 执行失败: {str(tool_error)}"
                    LOGGER.error(error_message)

                    # 构建工具错误消息
                    tool_message = {
                        "role": "tool",
                        "content": f"错误: {error_message}",
                        "tool_call_id": tool_call.get("id", ""),
                    }
                    current_messages.append(tool_message)

                    yield {
                        "type": "tool_error",
                        "role": "tool",  # 添加角色信息
                        "tool_name": tool_name,
                        "error": error_message,
                    }

            if stop_on_first_tool:
                # 如果设置了在第一次工具调用后停止，则停止迭代
                break

            # 短暂暂停，避免过快发送请求
            await asyncio.sleep(0.1)
        print("\n--------------------------------")
        print(current_messages)
        # 达到最大迭代次数
        if iteration == self.max_iterations - 1:
            LOGGER.warning("达到最大迭代次数 %s", self.max_iterations)
            yield {
                "type": "max_iterations_reached",
                "role": "system",  # 添加角色信息（系统消息）
                "max_iterations": self.max_iterations,
            }


# 创建一个示例脚本来演示多轮工具调用
async def demo_multi_tool_calls():
    """演示多轮工具调用"""
    # pylint: disable=import-outside-toplevel
    from .factory import AIModelType, FACTORY
    from .tools.general import CalculatorTool, SearchTool, WeatherTool

    # 注册工具
    REGISTRY.register(CalculatorTool)
    REGISTRY.register(SearchTool)
    REGISTRY.register(WeatherTool)

    # 创建AI客户端
    client = FACTORY.create_client(AIModelType.QWEN)

    # 创建Agent服务
    agent = AgentService(client, debug=True)

    # 定义系统提示
    system_prompt = """你是一个有用的助手。你可以使用提供的工具来帮助用户解决问题。
当需要计算时，使用calculatortool工具。
当需要查询天气时，使用weathertool工具。
当需要搜索信息时，使用searchtool工具。
"""

    # 定义用户消息
    messages = [{
        "role": "user",
        "content": "北京今天的气温是多少摄氏度？然后帮我计算(气温 - 10) * 2是多少？",
    }]

    # 运行Agent
    updated_messages, tool_results = await agent.run(
        messages=messages,
        system_prompt=system_prompt,
    )

    # 打印结果
    print("\n=== 对话历史 ===")
    for message in updated_messages:
        role = message["role"]
        content = message.get("content", "")
        print(f"\n[{role}]: {content}")

        if "tool_calls" in message:
            for tool_call in message["tool_calls"]:
                function = tool_call["function"]
                print(f"  调用工具: {function['name']}")
                print(
                    f"  参数: {json.dumps(function['arguments'], ensure_ascii=False)}"
                )

    print("\n=== 工具调用结果 ===")
    for result in tool_results:
        print(f"\n工具: {result['tool_name']}")
        print(f"参数: {json.dumps(result['arguments'], ensure_ascii=False)}")
        print(f"结果: {json.dumps(result['result'], ensure_ascii=False)}")

    # 关闭客户端
    await client.close()
