"""工具基础类和接口定义。"""

import inspect
import re
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, get_type_hints

from pydantic import BaseModel


class ToolType(str, Enum):
    """工具类型枚举"""

    FUNCTION = "function"
    ACTION = "action"
    DATA_SOURCE = "data_source"


class ToolParameter(BaseModel):
    """工具参数模型"""

    name: str
    type: str
    description: str
    required: bool = False
    enum: Optional[List[Any]] = None
    default: Optional[Any] = None


class ToolSchema(BaseModel):
    """工具模式定义"""

    name: str
    description: str
    type: ToolType = ToolType.FUNCTION
    parameters: Dict[str, ToolParameter] = {}


class BaseTool(ABC):
    """工具抽象基类"""

    @classmethod
    def get_name(cls) -> str:
        """获取工具名称"""
        return cls.__name__.lower()

    @classmethod
    def get_description(cls) -> str:
        """获取工具描述"""
        return cls.__doc__ or "No description provided"

    @classmethod
    def get_type(cls) -> ToolType:
        """获取工具类型"""
        return ToolType.FUNCTION

    @classmethod
    def get_parameters(cls) -> Dict[str, ToolParameter]:
        """获取工具参数"""
        # 获取执行方法的签名
        method = getattr(cls, "execute")
        signature = inspect.signature(method)
        doc = inspect.getdoc(method) or ""

        parameters = {}
        type_hints = get_type_hints(method)

        # 解析方法参数
        for name, param in signature.parameters.items():
            if name == "self":
                continue

            param_type = type_hints.get(name, Any).__name__
            description = ""
            required = param.default == inspect.Parameter.empty
            default = None if required else param.default
            enum_values = None

            # 尝试从文档字符串中提取参数描述
            param_doc_match = None

            param_pattern = rf":param\s+{name}:\s*(.*?)(?=:param|:return|$)"
            param_doc_match = re.search(param_pattern, doc, re.DOTALL)

            if param_doc_match:
                description = param_doc_match.group(1).strip()

            # 检查是否为枚举类型
            if hasattr(type_hints.get(name, None), "__members__"):
                enum_values = list(type_hints[name].__members__.keys())

            parameters[name] = ToolParameter(
                name=name,
                type=param_type,
                description=description,
                required=required,
                enum=enum_values,
                default=default,
            )

        return parameters

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """获取工具的JSON Schema定义"""
        parameters = cls.get_parameters()

        # 构建JSON Schema
        properties = {}
        required_params = []

        for name, param in parameters.items():
            prop = {
                "type": param.type,
                "description": param.description,
            }

            if param.enum:
                prop["enum"] = param.enum

            properties[name] = prop

            if param.required:
                required_params.append(name)

        schema = {
            "type": "function",
            "function": {
                "name": cls.get_name(),
                "description": cls.get_description(),
                "parameters": {
                    "type": "object",
                    "properties": properties,
                },
            },
        }

        if required_params:
            schema["function"]["parameters"]["required"] = required_params

        return schema

    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        """
        执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            工具执行结果
        """
        pass
