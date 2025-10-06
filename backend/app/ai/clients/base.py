"""AI客户端基础类定义。"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, AsyncIterator, Dict, List, Optional, Union


class Role(str, Enum):
    """消息角色枚举"""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


class Message(Dict[str, Any]):
    """消息类型，包含角色和内容"""

    pass


class ToolCall(Dict[str, Any]):
    """工具调用类型"""

    pass


class StreamingResponse(Dict[str, Any]):
    """流式响应类型"""

    pass


class AIClientOptions(Dict[str, Any]):
    """AI客户端选项"""

    pass


class BaseAIClient(ABC):
    """AI客户端抽象基类"""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[AIClientOptions] = None,
        stream: bool = True,
    ) -> Union[str, AsyncIterator[StreamingResponse]]:
        """
        生成文本

        Args:
            prompt: 提示文本
            system_prompt: 系统提示
            options: 生成选项
            stream: 是否流式输出

        Returns:
            如果stream=True，返回StreamingResponse的异步迭代器
            如果stream=False，返回生成的完整文本
        """
        pass

    @abstractmethod
    async def chat(
        self,
        messages: List[Message],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        options: Optional[AIClientOptions] = None,
        stream: bool = True,
    ) -> Union[Message, AsyncIterator[StreamingResponse]]:
        """
        聊天对话

        Args:
            messages: 对话历史
            system_prompt: 系统提示
            tools: 可用工具列表
            options: 生成选项
            stream: 是否流式输出

        Returns:
            如果stream=True，返回StreamingResponse的异步迭代器
            如果stream=False，返回生成的完整消息
        """
        pass

    @abstractmethod
    async def embeddings(
        self,
        texts: Union[str, List[str]],
        options: Optional[AIClientOptions] = None,
    ) -> List[List[float]]:
        """
        生成文本嵌入向量

        Args:
            texts: 单个文本或文本列表
            options: 生成选项

        Returns:
            嵌入向量列表
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """关闭客户端连接"""
        pass
