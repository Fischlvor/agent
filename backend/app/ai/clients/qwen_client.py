"""Qwen AI客户端实现。"""

import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Union

import httpx

from .base import AIClientOptions, BaseAIClient, Message, StreamingResponse

LOGGER = logging.getLogger(__name__)


class QwenClient(BaseAIClient):
    """千问AI客户端，基于本地Ollama实现

    职责划分：
    - 客户端层（本类）：仅负责与 Ollama API 通信，原样返回 API 响应
    - 业务层（AgentService）：负责判断是否使用工具、执行工具调用、管理对话流程

    设计原则：
    - 单一职责：只做 HTTP 通信和数据传输
    - 无状态：不保存对话历史或业务状态
    - 透明传输：不修改或解释 API 响应内容
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "qwen3:8b",  # Default model set to qwen3:8b
        timeout: float = 300.0,  # 增加到5分钟，支持复杂的知识库问答任务
        max_retries: int = 3,
    ):
        """
        初始化Qwen客户端

        Args:
            base_url: Ollama服务的基础URL
            model: 模型名称
            timeout: 请求超时时间
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        options: Optional[AIClientOptions] = None,
        stream: bool = True,
    ) -> Union[str, AsyncIterator[StreamingResponse]]:
        """
        生成文本

        职责：仅负责与 Ollama API 通信，返回生成的文本

        Args:
            prompt: 提示文本
            system_prompt: 系统提示
            options: 生成选项
            stream: 是否流式输出

        Returns:
            如果stream=True，返回StreamingResponse的异步迭代器
            如果stream=False，返回生成的完整文本
        """
        url = f"{self.base_url}/api/generate"

        # 构建请求数据
        data = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
        }

        if system_prompt:
            data["system"] = system_prompt

        if options:
            data["options"] = options

        if stream:
            return self._stream_generate(url, data)
        else:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("response", "")

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

        职责：仅负责与 Ollama API 通信，原样返回 API 响应
        不做任何业务逻辑判断（如工具调用处理）

        Args:
            messages: 对话历史
            system_prompt: 系统提示
            tools: 可用工具列表
            options: 生成选项
            stream: 是否流式输出

        Returns:
            如果stream=True，返回StreamingResponse的异步迭代器
            如果stream=False，返回完整的API响应（包含message字段）
        """
        url = f"{self.base_url}/api/chat"

        # 构建消息列表
        formatted_messages = []

        # 添加系统消息
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })

        # 添加对话历史
        for msg in messages:
            formatted_messages.append(msg)

        # 构建请求数据
        data = {
            "model": self.model,
            "messages": formatted_messages,
            "stream": stream,
        }

        # 添加工具定义
        if tools:
            data["tools"] = tools

        if options:
            data["options"] = options

        if stream:
            return self._stream_chat(url, data)
        else:
            # 非流式：直接返回 API 响应，让上层处理
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            result = response.json()

            # 直接返回 message 字段，保持与 Ollama API 一致
            # 上层（AgentService）负责判断和处理 tool_calls
            return result.get("message", {})

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
        url = f"{self.base_url}/api/embeddings"

        # 如果是单个文本，转换为列表
        if isinstance(texts, str):
            texts = [texts]

        # 构建请求数据
        data = {
            "model": self.model,
            "prompt": texts[0] if len(texts) == 1 else texts,
        }

        if options:
            data["options"] = options

        response = await self.client.post(url, json=data)
        response.raise_for_status()
        result = response.json()

        # 提取嵌入向量
        embedding = result.get("embedding", [])

        # 如果是多个文本，需要分别处理
        if len(texts) > 1:
            embeddings = []
            for text in texts:
                single_data = {
                    "model": self.model,
                    "prompt": text,
                }
                if options:
                    single_data["options"] = options

                single_response = await self.client.post(url, json=single_data)
                single_response.raise_for_status()
                single_result = single_response.json()
                embeddings.append(single_result.get("embedding", []))
            return embeddings
        else:
            return [embedding]

    async def close(self) -> None:
        """关闭客户端连接"""
        await self.client.aclose()

    async def _stream_generate(
        self,
        url: str,
        data: Dict[str, Any]
    ) -> AsyncIterator[StreamingResponse]:
        """
        流式生成文本（内部方法）

        职责：仅负责流式传输 API 数据，不做任何处理

        Args:
            url: API端点URL
            data: 请求数据

        Yields:
            原始的流式响应块（直接来自 Ollama API）
        """
        async with self.client.stream("POST", url, json=data) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError as e:
                        LOGGER.warning("解析流式响应失败: %s, 行: %s", str(e), line)

    async def _stream_chat(
        self,
        url: str,
        data: Dict[str, Any]
    ) -> AsyncIterator[StreamingResponse]:
        """
        流式聊天对话（内部方法）

        职责：仅负责流式传输 API 数据，不做任何处理

        Args:
            url: API端点URL
            data: 请求数据

        Yields:
            原始的流式响应块（直接来自 Ollama API）
        """
        async with self.client.stream("POST", url, json=data) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.strip():
                    try:
                        chunk = json.loads(line)
                        yield chunk
                    except json.JSONDecodeError as e:
                        LOGGER.warning("解析流式响应失败: %s, 行: %s", str(e), line)
