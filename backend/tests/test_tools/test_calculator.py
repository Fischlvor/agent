import asyncio

import pytest
from app.ai.tools.general.calculator import CalculatorTool


@pytest.fixture
def calculator():
    """创建计算器工具实例"""
    return CalculatorTool()


@pytest.mark.asyncio
async def test_basic_arithmetic(calculator):
    """测试基本算术运算"""
    # 加法
    result = await calculator.execute("2 + 2")
    assert result["result"] == 4
    assert result["formatted_result"] == "4"

    # 减法
    result = await calculator.execute("10 - 5")
    assert result["result"] == 5
    assert result["formatted_result"] == "5"

    # 乘法
    result = await calculator.execute("3 * 4")
    assert result["result"] == 12
    assert result["formatted_result"] == "12"

    # 除法
    result = await calculator.execute("10 / 2")
    assert result["result"] == 5
    assert result["formatted_result"] == "5"


@pytest.mark.asyncio
async def test_complex_expressions(calculator):
    """测试复杂表达式"""
    # 混合运算
    result = await calculator.execute("2 + 3 * 4")
    assert result["result"] == 14

    # 使用括号
    result = await calculator.execute("(2 + 3) * 4")
    assert result["result"] == 20

    # 浮点数
    result = await calculator.execute("3.14 * 2")
    assert result["result"] == 6.28
    assert result["formatted_result"] == "6.28"


@pytest.mark.asyncio
async def test_math_functions(calculator):
    """测试数学函数"""
    # 平方根
    result = await calculator.execute("sqrt(16)")
    assert result["result"] == 4

    # 三角函数
    result = await calculator.execute("sin(0)")
    assert result["result"] == 0

    # 指数
    result = await calculator.execute("pow(2, 3)")
    assert result["result"] == 8

    # 对数
    result = await calculator.execute("log(10)")
    assert abs(result["result"] - 2.302585092994046) < 1e-10


@pytest.mark.asyncio
async def test_error_handling(calculator):
    """测试错误处理"""
    # 除以零
    result = await calculator.execute("1 / 0")
    assert "error" in result
    assert "division by zero" in result["error"].lower()

    # 语法错误
    result = await calculator.execute("2 +* 3")
    assert "error" in result
    assert "syntax" in result["error"].lower()


@pytest.mark.asyncio
async def test_security(calculator):
    """测试安全性"""
    # 尝试执行危险代码
    result = await calculator.execute("__import__('os').system('echo hack')")
    assert "error" in result
    assert "不安全" in result["error"]

    # 尝试赋值
    result = await calculator.execute("x = 5")
    assert "error" in result
    assert "赋值" in result["error"]
