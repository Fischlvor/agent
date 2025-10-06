from typing import Any, Dict

import pytest
from app.ai.tools.base import BaseTool
from app.ai.tools.registry import ToolRegistry


# 创建测试用的工具类
class TestTool1(BaseTool):
    """测试工具1"""

    async def execute(self, param1: str, param2: int = 0) -> Dict[str, Any]:
        """
        测试方法

        :param param1: 测试参数1
        :param param2: 测试参数2
        :return: 测试结果
        """
        return {"param1": param1, "param2": param2}


class TestTool2(BaseTool):
    """测试工具2"""

    async def execute(self, value: float) -> Dict[str, Any]:
        """
        测试方法

        :param value: 测试值
        :return: 测试结果
        """
        return {"result": value * 2}


@pytest.fixture
def registry():
    """创建工具注册表实例"""
    return ToolRegistry()


def test_register_and_get_tool(registry):
    """测试注册和获取工具"""
    # 注册工具
    registry.register(TestTool1)
    registry.register(TestTool2)

    # 获取工具类
    tool1_class = registry.get_tool("testtool1")
    tool2_class = registry.get_tool("testtool2")

    assert tool1_class == TestTool1
    assert tool2_class == TestTool2

    # 获取不存在的工具
    assert registry.get_tool("nonexistent") is None


def test_get_instance(registry):
    """测试获取工具实例"""
    # 注册工具
    registry.register(TestTool1)

    # 获取工具实例
    tool1_instance = registry.get_instance("testtool1")

    assert isinstance(tool1_instance, TestTool1)

    # 再次获取应该返回相同的实例
    tool1_instance2 = registry.get_instance("testtool1")
    assert tool1_instance is tool1_instance2

    # 获取不存在的工具实例
    assert registry.get_instance("nonexistent") is None


def test_unregister(registry):
    """测试取消注册工具"""
    # 注册工具
    registry.register(TestTool1)
    assert "testtool1" in registry.get_all_tools()

    # 取消注册
    registry.unregister("testtool1")
    assert "testtool1" not in registry.get_all_tools()

    # 取消注册不存在的工具不应抛出异常
    registry.unregister("nonexistent")


def test_get_all_tools(registry):
    """测试获取所有工具"""
    # 注册工具
    registry.register(TestTool1)
    registry.register(TestTool2)

    # 获取所有工具
    all_tools = registry.get_all_tools()

    assert len(all_tools) == 2
    assert "testtool1" in all_tools
    assert "testtool2" in all_tools
    assert all_tools["testtool1"] == TestTool1
    assert all_tools["testtool2"] == TestTool2


def test_get_all_schemas(registry):
    """测试获取所有工具的JSON Schema定义"""
    # 注册工具
    registry.register(TestTool1)
    registry.register(TestTool2)

    # 获取所有工具的JSON Schema定义
    schemas = registry.get_all_schemas()

    assert len(schemas) == 2

    # 验证第一个工具的Schema
    tool1_schema = next(s for s in schemas if s["function"]["name"] == "testtool1")
    assert tool1_schema["type"] == "function"
    assert "param1" in tool1_schema["function"]["parameters"]["properties"]
    assert "param2" in tool1_schema["function"]["parameters"]["properties"]

    # 验证第二个工具的Schema
    tool2_schema = next(s for s in schemas if s["function"]["name"] == "testtool2")
    assert tool2_schema["type"] == "function"
    assert "value" in tool2_schema["function"]["parameters"]["properties"]
