import asyncio
import json
import os
import sys

sys.path.append(".")

from app.ai.function_calling import FunctionCallingHandler, FunctionCallParser
from app.ai.tools.general import CalculatorTool
from app.ai.tools.registry import registry


async def main():
    # 注册计算器工具
    registry.register(CalculatorTool)

    # 创建函数调用解析器和处理器
    parser = FunctionCallParser()
    handler = FunctionCallingHandler(parser)

    try:
        # 测试不同格式的函数调用解析
        print("=== 函数调用解析测试 ===")

        # 格式1: {{function_name(param1="value1", param2="value2")}}
        text1 = '我需要计算2加2等于多少: {{calculatortool(expression="2 + 2")}}'
        function_calls1 = parser.extract_function_calls(text1)
        print("\n格式1解析结果:")
        print(json.dumps(function_calls1, ensure_ascii=False, indent=2))

        # 格式2: function_name(param1="value1", param2="value2")
        text2 = '我需要计算3乘4等于多少: calculatortool(expression="3 * 4")'
        function_calls2 = parser.extract_function_calls(text2)
        print("\n格式2解析结果:")
        print(json.dumps(function_calls2, ensure_ascii=False, indent=2))

        # 格式3: {"name": "function_name", "arguments": {"param1": "value1"}}
        text3 = '我需要计算平方根: {"name": "calculatortool", "arguments": {"expression": "sqrt(16)"}}'
        function_calls3 = parser.extract_function_calls(text3)
        print("\n格式3解析结果:")
        print(json.dumps(function_calls3, ensure_ascii=False, indent=2))

        # 测试函数调用处理
        print("\n=== 函数调用处理测试 ===")

        # 处理字符串响应
        text = '让我计算一下: {{calculatortool(expression="10 / 2")}}'
        response_text, results = await handler.process_response(text)
        print("\n处理字符串响应:")
        print(f"原始文本: {response_text}")
        print("处理结果:")
        print(json.dumps(results, ensure_ascii=False, indent=2))

        # 处理字典响应
        dict_response = {
            "content": "让我计算一下",
            "tool_calls": [
                {
                    "function": {
                        "name": "calculatortool",
                        "arguments": {"expression": "5 * 5"},
                    }
                }
            ],
        }
        response_text, results = await handler.process_response(dict_response)
        print("\n处理字典响应:")
        print(f"原始文本: {response_text}")
        print("处理结果:")
        print(json.dumps(results, ensure_ascii=False, indent=2))

    finally:
        # 取消注册工具
        registry.unregister("calculatortool")


if __name__ == "__main__":
    asyncio.run(main())
