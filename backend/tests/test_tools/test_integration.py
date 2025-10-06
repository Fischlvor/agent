import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.append(".")

from app.ai import (AIModelType, factory, function_calling_handler,
                    tool_registry)
from app.ai.tools.general import CalculatorTool


@pytest.fixture
def mock_client():
    """创建模拟的AI客户端"""
    mock = AsyncMock()

    # 模拟chat方法返回包含函数调用的响应
    mock.chat.return_value = {
        "content": "让我帮你计算2+2的结果",
        "tool_calls": [
            {
                "function": {
                    "name": "calculatortool",
                    "arguments": {"expression": "2 + 2"},
                }
            }
        ],
    }

    return mock


@pytest.fixture
def setup_environment():
    """设置测试环境"""
    # 注册计算器工具
    tool_registry.register(CalculatorTool)

    # 测试后清理
    yield

    # 取消注册工具
    tool_registry.unregister("calculatortool")


@pytest.mark.asyncio
async def test_integration_function_calling(mock_client, setup_environment):
    """测试函数调用的集成流程"""
    # 打补丁替换工厂的create_client方法
    with patch.object(factory, "create_client", return_value=mock_client):
        # 创建客户端
        client = factory.create_client(AIModelType.QWEN)

        # 准备消息和工具
        messages = [{"role": "user", "content": "计算2+2等于多少？"}]
        tools = tool_registry.get_all_schemas()

        # 执行聊天
        response = await client.chat(messages=messages, tools=tools, stream=False)

        # 处理响应和函数调用
        response_text, tool_results = await function_calling_handler.process_response(
            response
        )

        # 验证结果
        assert "让我帮你计算2+2的结果" in response_text
        assert len(tool_results) == 1
        assert tool_results[0]["tool_name"] == "calculatortool"
        assert tool_results[0]["result"]["result"] == 4


@pytest.mark.asyncio
async def test_streaming_function_calling(mock_client, setup_environment):
    """测试流式函数调用的集成流程"""

    # 模拟流式响应
    async def mock_stream():
        yield {"message": {"role": "assistant", "content": "让我帮你"}}
        yield {"message": {"role": "assistant", "content": "计算"}}
        yield {
            "message": {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "function": {
                            "name": "calculatortool",
                            "arguments": {"expression": "2 + 2"},
                        }
                    }
                ],
            }
        }

    # 设置模拟客户端返回流式响应
    mock_client.chat.return_value = mock_stream()

    # 打补丁替换工厂的create_client方法
    with patch.object(factory, "create_client", return_value=mock_client):
        # 创建客户端
        client = factory.create_client(AIModelType.QWEN)

        # 准备消息和工具
        messages = [{"role": "user", "content": "计算2+2等于多少？"}]
        tools = tool_registry.get_all_schemas()

        # 执行聊天
        response_stream = await client.chat(messages=messages, tools=tools, stream=True)

        # 处理流式响应
        chunks = []
        async for chunk in function_calling_handler.process_streaming_response(
            response_stream
        ):
            chunks.append(chunk)

        # 验证结果
        assert len(chunks) == 3
        assert "tool_results" in chunks[2]
        assert chunks[2]["tool_results"]["calculatortool"]["result"] == 4
