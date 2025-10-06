#!/usr/bin/env python3
"""测试 Ollama 流式响应格式，验证 tool_calls 如何出现在流式响应中"""

import asyncio
import json
import os
import sys

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from app.ai.clients.qwen_client import QwenClient  # pylint: disable=import-error


async def test_stream_without_tools():
    """测试没有工具调用的流式响应"""
    print("\n=== 测试1: 没有工具调用的流式响应 ===\n")

    client = QwenClient()

    try:
        messages = [{"role": "user", "content": "请写一首关于春天的短诗"}]

        chunk_count = 0
        async for chunk in await client.chat(messages=messages, stream=True):
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(f"  完整内容: {json.dumps(chunk, ensure_ascii=False)}")

            if "message" in chunk:
                message = chunk["message"]
                content = message.get("content", "")
                if content:
                    print(f"  内容: {content}")

            if "done" in chunk:
                print(f"  done: {chunk['done']}")

            print()

        print(f"总共收到 {chunk_count} 个 chunks\n")

    finally:
        await client.close()


async def test_stream_with_tools():
    """测试有工具调用的流式响应"""
    print("\n=== 测试2: 有工具调用的流式响应 ===\n")

    client = QwenClient()

    try:
        # 定义一个简单的工具
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "城市名称，例如：北京、上海"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

        messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

        chunk_count = 0
        has_tool_calls = False
        tool_calls_chunk_number = None

        async for chunk in await client.chat(messages=messages, tools=tools, stream=True):
            chunk_count += 1
            print(f"Chunk {chunk_count}:")
            print(f"  完整内容: {json.dumps(chunk, ensure_ascii=False, indent=2)}")

            if "message" in chunk:
                message = chunk["message"]

                # 检查内容
                content = message.get("content", "")
                if content:
                    print(f"  内容: {content}")

                # 检查工具调用
                if "tool_calls" in message and message["tool_calls"]:
                    has_tool_calls = True
                    tool_calls_chunk_number = chunk_count
                    print(f"  !!! 发现 tool_calls: {json.dumps(message['tool_calls'], ensure_ascii=False)}")

            if "done" in chunk:
                print(f"  done: {chunk['done']}")

            print()

        print(f"总共收到 {chunk_count} 个 chunks")
        if has_tool_calls:
            print(f"tool_calls 出现在第 {tool_calls_chunk_number} 个 chunk 中")
        else:
            print("没有工具调用")
        print()

    finally:
        await client.close()


async def test_non_stream_with_tools():
    """测试非流式响应（对比）"""
    print("\n=== 测试3: 非流式响应（对比） ===\n")

    client = QwenClient()

    try:
        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_weather",
                    "description": "获取指定城市的天气信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "城市名称，例如：北京、上海"
                            }
                        },
                        "required": ["location"]
                    }
                }
            }
        ]

        messages = [{"role": "user", "content": "北京今天天气怎么样？"}]

        response = await client.chat(messages=messages, tools=tools, stream=False)

        print("完整响应:")
        print(json.dumps(response, ensure_ascii=False, indent=2))
        print()

        if "tool_calls" in response:
            print("✓ 包含 tool_calls")
        else:
            print("✗ 不包含 tool_calls")

    finally:
        await client.close()


async def main():
    """主函数"""
    print("\n" + "="*60)
    print("Ollama 流式响应格式测试")
    print("="*60)

    try:
        # 测试1：没有工具的流式响应
        await test_stream_without_tools()

        # 测试2：有工具的流式响应
        await test_stream_with_tools()

        # 测试3：非流式响应对比
        await test_non_stream_with_tools()

        print("\n" + "="*60)
        print("关键发现：")
        print("1. 流式响应中，content 会分散在多个 chunk 中")
        print("2. tool_calls 只会出现在最后一个 chunk (done: true) 中")
        print("3. 需要累积所有 chunk 才能获取完整的 tool_calls 信息")
        print("="*60)

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

