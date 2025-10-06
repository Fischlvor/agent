#!/usr/bin/env python3
"""显示工具注册的输出"""

import json
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.ai.tools.general import CalculatorTool, SearchTool, WeatherTool
from app.ai.tools.registry import registry


def main():
    """主函数"""
    print("=== 注册工具并显示Schema ===")

    # 注册工具
    registry.register(CalculatorTool)
    registry.register(SearchTool)
    registry.register(WeatherTool)

    # 显示已注册的工具
    tools = registry.get_all_tools()
    print(f"已注册的工具: {', '.join(tools.keys())}")

    # 获取工具的Schema
    schemas = registry.get_all_schemas()
    print(schemas)


if __name__ == "__main__":
    main()
