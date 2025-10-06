"""工具系统初始化"""

from . import general
from .base import BaseTool
from .registry import REGISTRY


# 自动注册通用工具
def register_default_tools():
    """注册默认工具"""
    # 导入所有工具模块，确保工具类已定义
    # from .general import CalculatorTool, SearchTool, WeatherTool

    # 注册工具
    # registry.register(CalculatorTool)
    # registry.register(SearchTool)
    # registry.register(WeatherTool)

    # 也可以使用自动发现机制
    REGISTRY.auto_discover("app.ai.tools.general")


# 在导入时自动注册默认工具
register_default_tools()

__all__ = ["REGISTRY", "BaseTool", "register_default_tools"]
