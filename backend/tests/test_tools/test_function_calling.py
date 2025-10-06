import json
from typing import Any, Dict, List

import pytest
from app.ai.function_calling import FunctionCallingHandler, FunctionCallParser


@pytest.fixture
def parser():
    """创建函数调用解析器实例"""
    return FunctionCallParser()


@pytest.fixture
def handler():
    """创建函数调用处理器实例"""
    return FunctionCallingHandler()


def test_extract_function_calls_format1(parser):
    """测试提取格式1的函数调用: {{function_name(param1="value1", param2="value2")}}"""
    text = """
    这是一个测试文本，包含函数调用 {{get_weather(location="Beijing", unit="celsius")}}
    还有其他内容。
    """

    function_calls = parser.extract_function_calls(text)

    assert len(function_calls) == 1
    assert function_calls[0]["function"]["name"] == "get_weather"
    assert function_calls[0]["function"]["arguments"]["location"] == "Beijing"
    assert function_calls[0]["function"]["arguments"]["unit"] == "celsius"


def test_extract_function_calls_format2(parser):
    """测试提取格式2的函数调用: function_name(param1="value1", param2="value2")"""
    text = """
    这是一个测试文本，包含函数调用 calculate(expression="2 + 2")
    还有其他内容。
    """

    function_calls = parser.extract_function_calls(text)

    assert len(function_calls) == 1
    assert function_calls[0]["function"]["name"] == "calculate"
    assert function_calls[0]["function"]["arguments"]["expression"] == "2 + 2"


def test_extract_function_calls_format3(parser):
    """测试提取格式3的函数调用: {"name": "function_name", "arguments": {"param1": "value1"}}"""
    text = """
    这是一个测试文本，包含函数调用 {"name": "search", "arguments": {"query": "Python", "num_results": 5}}
    还有其他内容。
    """

    function_calls = parser.extract_function_calls(text)

    assert len(function_calls) == 1
    assert function_calls[0]["function"]["name"] == "search"
    assert function_calls[0]["function"]["arguments"]["query"] == "Python"
    assert function_calls[0]["function"]["arguments"]["num_results"] == 5


def test_extract_multiple_function_calls(parser):
    """测试提取多个函数调用"""
    text = """
    这是一个测试文本，包含多个函数调用:
    1. {{get_weather(location="Beijing", unit="celsius")}}
    2. calculate(expression="2 + 2")
    3. {"name": "search", "arguments": {"query": "Python", "num_results": 5}}
    """

    function_calls = parser.extract_function_calls(text)

    assert len(function_calls) == 3

    # 验证第一个函数调用
    assert function_calls[0]["function"]["name"] == "get_weather"
    assert function_calls[0]["function"]["arguments"]["location"] == "Beijing"

    # 验证第二个函数调用
    assert function_calls[1]["function"]["name"] == "calculate"
    assert function_calls[1]["function"]["arguments"]["expression"] == "2 + 2"

    # 验证第三个函数调用
    assert function_calls[2]["function"]["name"] == "search"
    assert function_calls[2]["function"]["arguments"]["query"] == "Python"


def test_parse_key_value_args(parser):
    """测试解析键值对格式的参数字符串"""
    # 测试字符串参数
    args = 'param1="value1", param2="value2"'
    parsed = parser._parse_key_value_args(args)

    assert parsed["param1"] == "value1"
    assert parsed["param2"] == "value2"

    # 测试数字参数
    args = "num1=42, num2=3.14"
    parsed = parser._parse_key_value_args(args)

    assert parsed["num1"] == 42
    assert parsed["num2"] == 3.14

    # 测试布尔参数
    args = "flag1=true, flag2=false"
    parsed = parser._parse_key_value_args(args)

    assert parsed["flag1"] is True
    assert parsed["flag2"] is False

    # 测试混合参数
    args = 'name="test", value=123, enabled=true'
    parsed = parser._parse_key_value_args(args)

    assert parsed["name"] == "test"
    assert parsed["value"] == 123
    assert parsed["enabled"] is True


@pytest.mark.asyncio
async def test_process_response_string(handler, monkeypatch):
    """测试处理字符串响应"""

    # 模拟工具执行
    async def mock_execute_tool_call(tool_call):
        function_name = tool_call["function"]["name"]
        return function_name, {"result": "mock_result"}

    # 打补丁替换工具执行方法
    from app.ai.tools.executor import executor

    monkeypatch.setattr(executor, "execute_tool_call", mock_execute_tool_call)

    # 测试字符串响应
    response = '这是一个测试响应，包含函数调用 {{get_weather(location="Beijing")}}'

    response_text, results = await handler.process_response(response)

    assert "这是一个测试响应，包含函数调用" in response_text
    assert len(results) == 1
    assert results[0]["tool_name"] == "get_weather"
    assert results[0]["result"]["result"] == "mock_result"


@pytest.mark.asyncio
async def test_process_response_dict(handler, monkeypatch):
    """测试处理字典响应"""

    # 模拟工具执行
    async def mock_execute_tool_call(tool_call):
        function_name = tool_call["function"]["name"]
        return function_name, {"result": "mock_result"}

    # 打补丁替换工具执行方法
    from app.ai.tools.executor import executor

    monkeypatch.setattr(executor, "execute_tool_call", mock_execute_tool_call)

    # 测试字典响应
    response = {
        "content": "这是一个测试响应",
        "tool_calls": [
            {"function": {"name": "get_weather", "arguments": {"location": "Beijing"}}}
        ],
    }

    response_text, results = await handler.process_response(response)

    assert response_text == "这是一个测试响应"
    assert len(results) == 1
    assert results[0]["tool_name"] == "get_weather"
    assert results[0]["result"]["result"] == "mock_result"
