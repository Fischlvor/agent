"""计算器工具模块。"""

import logging
import math
from typing import Any, Dict, Union

from ..base import BaseTool

LOGGER = logging.getLogger(__name__)


class CalculatorTool(BaseTool):
    """计算器工具，用于执行基本数学运算"""

    async def execute(
        self,
        expression: str,
    ) -> Dict[str, Any]:
        """
        执行数学表达式计算

        :param expression: 要计算的数学表达式，如 "2 + 2 * 3"
        :return: 包含计算结果和过程的字典
        """
        LOGGER.info("计算表达式: %s", expression)

        try:
            # 创建安全的局部环境，只允许使用有限的数学函数
            safe_dict = {
                "abs": abs,
                "round": round,
                "min": min,
                "max": max,
                "sum": sum,
                "pow": pow,
                "int": int,
                "float": float,
                "sin": math.sin,
                "cos": math.cos,
                "tan": math.tan,
                "asin": math.asin,
                "acos": math.acos,
                "atan": math.atan,
                "sqrt": math.sqrt,
                "log": math.log,
                "log10": math.log10,
                "exp": math.exp,
                "pi": math.pi,
                "e": math.e,
            }

            # 检查表达式是否安全
            self._check_expression_safety(expression)

            # 计算表达式
            result = eval(expression, {"__builtins__": {}}, safe_dict)

            # 格式化结果
            if isinstance(result, (int, float)):
                formatted_result = self._format_number(result)
            else:
                formatted_result = str(result)

            return {
                "expression": expression,
                "result": result,
                "formatted_result": formatted_result,
            }

        except Exception as e:
            error_message = f"计算错误: {str(e)}"
            LOGGER.error(error_message)
            return {"expression": expression, "error": error_message}

    def _check_expression_safety(self, expression: str) -> None:
        """
        检查表达式是否安全

        :param expression: 要检查的表达式
        :raises ValueError: 如果表达式包含不安全的代码
        """
        # 检查是否包含危险的内置函数或模块
        dangerous_terms = [
            "__import__",
            "import",
            "eval",
            "exec",
            "compile",
            "open",
            "file",
            "os.",
            "sys.",
            "subprocess",
            "shutil",
            "globals",
            "locals",
            "getattr",
            "setattr",
            "delattr",
        ]

        for term in dangerous_terms:
            if term in expression:
                raise ValueError(f"表达式包含不安全的代码: {term}")

        # 检查是否有赋值操作
        if "=" in expression and not "==" in expression:
            raise ValueError("表达式不能包含赋值操作")

    def _format_number(self, number: Union[int, float]) -> str:
        """
        格式化数字，去除不必要的小数点和零

        :param number: 要格式化的数字
        :return: 格式化后的字符串
        """
        if isinstance(number, int) or number.is_integer():
            return str(int(number))
        else:
            # 限制小数位数，避免浮点精度问题
            return f"{number:.10f}".rstrip("0").rstrip(".")
