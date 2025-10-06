"""测试千问3模型的工具调用功能"""

import asyncio
import json
import logging
import os
import sys
from typing import Any, Dict

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.ai.clients.qwen_client import QwenClient
from app.ai.tools.general import CalculatorTool, SearchTool, WeatherTool
from app.ai.tools.registry import registry

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def register_all_tools():
    """注册所有可用工具"""
    registry.register(CalculatorTool)
    registry.register(SearchTool)
    registry.register(WeatherTool)

    # 打印已注册的工具
    tools = registry.get_all_tools()
    print(f"已注册的工具: {', '.join(tools.keys())}")

    return registry.get_all_schemas()


async def test_qwen_tool_calling(model_name: str = "qwen3:8b"):
    """测试千问模型的工具调用功能"""
    print(f"=== 测试 {model_name} 的工具调用功能 ===")

    # 注册所有工具
    tool_schemas = register_all_tools()

    # 创建客户端实例
    client = QwenClient(model=model_name)

    try:
        # 定义系统提示
        system_prompt = """你是一个有用的助手。根据用户的需求选择合适的工具
"""

        # 用户消息
        messages = [{"role": "user", "content": "计算23乘以45是多少？"}]

        print("发送请求...")
        print(f"系统提示: {system_prompt}")
        print(f"用户消息: {messages[0]['content']}")
        print(
            f"可用工具: {', '.join([tool['function']['name'] for tool in tool_schemas])}"
        )

        # 发送请求
        response = await client.chat(
            messages=messages,
            system_prompt=system_prompt,
            tools=tool_schemas,
            stream=False,
        )

        print("\n模型响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))

        # 检查是否包含工具调用
        if "tool_calls" in response:
            print("\n检测到工具调用:")
            for tool_call in response["tool_calls"]:
                print(f"工具名称: {tool_call['function']['name']}")
                print(
                    f"工具参数: {json.dumps(tool_call['function']['arguments'], ensure_ascii=False)}"
                )

                # 执行工具调用
                tool_name = tool_call["function"]["name"]
                arguments = tool_call["function"][
                    "arguments"
                ]  # 已经是字典，不需要json.loads

                tool_instance = registry.get_instance(tool_name)
                if tool_instance:
                    print(f"\n执行工具 {tool_name}...")
                    result = await tool_instance.execute(**arguments)
                    print(f"工具执行结果: {json.dumps(result, ensure_ascii=False)}")

            print("\n结论: 该模型支持工具调用！")
        else:
            print("\n未检测到工具调用，模型可能未正确理解或不支持工具调用。")

    finally:
        # 关闭客户端
        await client.close()
        print("=== 测试完成 ===")


async def test_weather_query():
    """测试天气查询"""
    print("=== 测试天气查询 ===")

    # 注册所有工具
    tool_schemas = register_all_tools()

    client = QwenClient(model="qwen3:8b")

    try:
        system_prompt = """你是一个有用的助手。根据用户的需求选择合适的工具
"""

        messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

        print("发送请求...")
        print(f"用户消息: {messages[0]['content']}")

        response = await client.chat(
            messages=messages,
            system_prompt=system_prompt,
            tools=tool_schemas,
            stream=False,
        )

        print("\n模型响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))

        # 检查是否包含工具调用
        if "tool_calls" in response:
            print("\n检测到工具调用:")
            for tool_call in response["tool_calls"]:
                print(f"工具名称: {tool_call['function']['name']}")
                print(
                    f"工具参数: {json.dumps(tool_call['function']['arguments'], ensure_ascii=False)}"
                )

                # 执行工具调用
                tool_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]

                tool_instance = registry.get_instance(tool_name)
                if tool_instance:
                    print(f"\n执行工具 {tool_name}...")
                    result = await tool_instance.execute(**arguments)
                    print(f"工具执行结果: {json.dumps(result, ensure_ascii=False)}")

    finally:
        await client.close()
        print("=== 测试完成 ===")


async def test_search_query():
    """测试搜索查询"""
    print("=== 测试搜索查询 ===")

    # 注册所有工具
    tool_schemas = register_all_tools()

    client = QwenClient(model="qwen3:8b")

    try:
        system_prompt = """你是一个有用的助手。根据用户的需求选择合适的工具
"""

        messages = [{"role": "user", "content": "搜索关于人工智能的最新进展"}]

        print("发送请求...")
        print(f"用户消息: {messages[0]['content']}")

        response = await client.chat(
            messages=messages,
            system_prompt=system_prompt,
            tools=tool_schemas,
            stream=False,
        )

        print("\n模型响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))

        # 检查是否包含工具调用
        if "tool_calls" in response:
            print("\n检测到工具调用:")
            for tool_call in response["tool_calls"]:
                print(f"工具名称: {tool_call['function']['name']}")
                print(
                    f"工具参数: {json.dumps(tool_call['function']['arguments'], ensure_ascii=False)}"
                )

                # 执行工具调用
                tool_name = tool_call["function"]["name"]
                arguments = tool_call["function"]["arguments"]

                tool_instance = registry.get_instance(tool_name)
                if tool_instance:
                    print(f"\n执行工具 {tool_name}...")
                    result = await tool_instance.execute(**arguments)
                    print(f"工具执行结果: {json.dumps(result, ensure_ascii=False)}")

    finally:
        await client.close()
        print("=== 测试完成 ===")


if __name__ == "__main__":
    # 获取命令行参数
    import argparse

    parser = argparse.ArgumentParser(description="测试千问模型的工具调用功能")
    parser.add_argument("--model", default="qwen3:8b", help="要测试的模型名称")
    parser.add_argument(
        "--test",
        default="calculator",
        choices=["calculator", "weather", "search", "all"],
        help="测试类型: calculator(计算器测试), weather(天气测试), search(搜索测试), all(所有测试)",
    )
    args = parser.parse_args()

    if args.test == "calculator" or args.test == "all":
        asyncio.run(test_qwen_tool_calling(args.model))

    if args.test == "weather" or args.test == "all":
        asyncio.run(test_weather_query())

    if args.test == "search" or args.test == "all":
        asyncio.run(test_search_query())
