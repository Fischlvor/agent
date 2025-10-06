#!/usr/bin/env python3
"""多轮工具调用演示"""

import asyncio
import json
import os
import sys
import traceback

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 导入ai.tools模块会自动注册所有工具
from app.ai.agent_service import AgentService  # pylint: disable=import-error
from app.ai.factory import AIModelType, FACTORY  # pylint: disable=import-error
from app.ai.tools.registry import REGISTRY  # pylint: disable=import-error
import app.ai.tools  # noqa: F401 # pylint: disable=import-error,wrong-import-position


async def demo_original_agent():
    """多轮工具调用演示"""
    print("=== 多轮工具调用演示 ===")

    # 打印已注册的工具
    tools = REGISTRY.get_all_tools()
    print(f"已注册的工具: {', '.join(tools.keys())}")

    # 创建AI客户端
    client = FACTORY.create_client(AIModelType.QWEN)

    # 创建Agent服务
    agent = AgentService(client, debug=True)

    # 定义系统提示
    system_prompt = """你是一个有用的助手。你可以使用提供的工具来帮助用户解决问题。
当需要计算时，使用calculatortool工具。
当需要查询天气时，使用weathertool工具。
当需要搜索信息时，使用searchtool工具。
请分步骤完成复杂的计算任务。"""

    # 定义用户消息 - 设计一个需要多轮工具调用的场景
    messages = [
        {
            "role": "user",
            "content": "广州今天的气温是多少摄氏度？如果温度合适，给我推荐一个玩的地方。",
        }
    ]

    print("\n开始执行Agent...")
    print(f"用户消息: {messages[0]['content']}")

    try:
        # 运行Agent（非流式）
        updated_messages, tool_results = await agent.run(
            messages=messages,
            system_prompt=system_prompt,
        )

        # 打印对话历史
        print("\n=== 对话历史 ===")
        for msg in updated_messages:
            role = msg["role"]
            content = msg.get("content", "")
            print(f"\n[{role}]: {content}")

            if "tool_calls" in msg:
                for tool_call in msg["tool_calls"]:
                    function = tool_call["function"]
                    print(f"  调用工具: {function['name']}")
                    print(f"  参数: {json.dumps(function['arguments'], ensure_ascii=False)}")

        # 打印工具调用结果
        print("\n=== 工具调用结果 ===")
        for result in tool_results:
            print(f"\n工具: {result['tool_name']}")
            print(f"参数: {json.dumps(result['arguments'], ensure_ascii=False)}")
            print(f"结果: {json.dumps(result['result'], ensure_ascii=False)}")

    finally:
        # 关闭客户端
        await client.close()


async def demo_streaming_agent():
    """流式多轮工具调用演示"""
    print("\n=== 流式多轮工具调用演示 ===")

    # 打印已注册的工具
    tools = REGISTRY.get_all_tools()
    print(f"已注册的工具: {', '.join(tools.keys())}")

    # 创建AI客户端
    client = FACTORY.create_client(AIModelType.QWEN)

    # 创建Agent服务
    agent = AgentService(client, debug=True)

    # 定义系统提示
    system_prompt = """你是一个有用的中文助手。你可以使用提供的工具来帮助用户解决问题。回答的结果必须是真实的、不能是没有依据的。"""

    # 定义用户消息
    messages = [
        {
            "role": "user",
            "content": "明天我想去玩广州玩，看看天气如何，给我推荐一个合适的去处。我们有两个大人一个小孩儿，给我预估一下费用",
        }
    ]

    print("\n开始执行流式Agent...")
    print(f"用户消息: {messages[0]['content']}")

    try:
        # 运行流式Agent
        content_started = False  # 标记是否已开始输出内容
        async for event in agent.run_streaming(
            messages=messages,
            system_prompt=system_prompt,
        ):
            event_type = event.get("type")

            if event_type == "content":
                # 流式输出内容
                role = event.get("role", "assistant")
                content = event.get("content", "")

                # 跳过空内容或只有空白字符的内容
                if not content or not content.strip():
                    continue

                # 首次输出时显示角色
                if not content_started:
                    print(f"\n\n[{role}]: ", end="", flush=True)
                    content_started = True
                print(content, end="", flush=True)

            elif event_type == "tool_calls":
                # 工具调用
                content_started = False  # 重置标记，下一轮会重新显示角色
                role = event.get("role", "assistant")
                tool_calls = event.get("tool_calls", [])
                print(f"\n\n[{role} - 工具调用]")
                for tool_call in tool_calls:
                    function = tool_call["function"]
                    print(f"  - {function['name']}: {json.dumps(function['arguments'], ensure_ascii=False)}")

            elif event_type == "tool_result":
                # 工具执行结果
                content_started = False  # 重置标记，下一轮会重新显示角色
                role = event.get("role", "tool")
                tool_name = event.get("tool_name")
                result = event.get("result")
                print(f"\n\n[{role} - 工具结果]")
                print(f"  - {tool_name}: {json.dumps(result, ensure_ascii=False)}")

            elif event_type == "tool_error":
                # 工具执行错误
                content_started = False  # 重置标记，下一轮会重新显示角色
                role = event.get("role", "tool")
                tool_name = event.get("tool_name")
                error = event.get("error")
                print(f"\n\n[{role} - 错误]")
                print(f"  - {tool_name}: {error}")

            elif event_type == "max_iterations_reached":
                # 达到最大迭代次数
                role = event.get("role", "system")
                print(f"\n\n[{role} - 警告] 达到最大迭代次数")

    finally:
        # 关闭客户端
        await client.close()


async def test_qwen_client_basic():
    """测试QwenClient基本功能"""
    print("\n=== 测试QwenClient基本功能 ===")

    # 创建客户端
    client = FACTORY.create_client(AIModelType.QWEN)

    try:
        # 测试非流式生成
        print("\n1. 测试非流式生成...")
        result = await client.generate(
            prompt="请用一句话介绍人工智能",
            stream=False
        )
        print(f"生成结果: {result}")

        # 测试非流式聊天
        print("\n2. 测试非流式聊天...")
        messages = [
            {"role": "user", "content": "你好，请介绍一下自己"}
        ]
        response = await client.chat(
            messages=messages,
            stream=False
        )
        print(f"聊天响应: {response}")

        # 测试流式聊天
        print("\n3. 测试流式聊天...")
        messages = [
            {"role": "user", "content": "请写一首关于春天的短诗"}
        ]
        print("流式输出: ", end="", flush=True)
        async for chunk in await client.chat(messages=messages, stream=True):
            if "message" in chunk:
                content = chunk["message"].get("content", "")
                if content:
                    print(content, end="", flush=True)
        print()  # 换行

    except Exception as e:  # pylint: disable=broad-except
        print(f"测试失败: {e}")
        traceback.print_exc()
    finally:
        await client.close()


async def main():
    """主函数"""
    try:
        # 可以选择运行不同的测试
        print("\n可用的测试:")
        print("1. 非流式Agent测试 (demo_original_agent)")
        print("2. 流式Agent测试 (demo_streaming_agent)")
        print("3. QwenClient基础功能测试 (test_qwen_client_basic)")
        print("4. 运行所有测试")

        # 默认运行第一个测试
        choice = input("\n请选择测试 (1-4, 默认为1): ").strip() or "1"

        if choice == "1":
            await demo_original_agent()
        elif choice == "2":
            await demo_streaming_agent()
        elif choice == "3":
            await test_qwen_client_basic()
        elif choice == "4":
            await test_qwen_client_basic()
            await demo_original_agent()
            await demo_streaming_agent()
        else:
            print(f"无效选择: {choice}")

    except KeyboardInterrupt:
        print("\n\n用户中断演示")
    except Exception as e:  # pylint: disable=broad-except
        print(f"\n演示过程中发生错误: {e}")
        traceback.print_exc()

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    asyncio.run(main())