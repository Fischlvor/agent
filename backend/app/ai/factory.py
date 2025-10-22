"""AI客户端工厂模块，用于创建不同类型的AI客户端。"""

import logging
from typing import Dict, Optional

from .clients.base import BaseAIClient
from .clients.qwen_client import QwenClient

LOGGER = logging.getLogger(__name__)


class AIClientFactory:
    """AI客户端工厂，用于创建不同的AI客户端实例"""

    def __init__(self):
        """初始化AI客户端工厂"""
        # Provider 到客户端类的映射
        self.client_classes = {
            "ollama": QwenClient,  # Ollama 使用 QwenClient
            # 未来可以添加更多 provider:
            # "openai": OpenAIClient,
            # "anthropic": AnthropicClient,
        }

        # 缓存已创建的客户端实例
        self._clients: Dict[str, BaseAIClient] = {}

    def create_client(
            self,
            provider: str,
            model_id: str,
            base_url: Optional[str] = None,
            **kwargs,
    ) -> BaseAIClient:
        """
        创建AI客户端实例

        Args:
            provider: 模型提供商，如 "ollama", "openai" 等
            model_id: 模型ID（API调用标识符），如 "qwen3:8b"
            base_url: API基础URL（可选）
            **kwargs: 传递给客户端构造函数的额外参数

        Returns:
            AI客户端实例

        Raises:
            ValueError: 如果provider不支持
        """
        # 规范化provider
        provider = provider.lower()

        # 检查provider是否支持
        if provider not in self.client_classes:
            supported_providers = ", ".join(self.client_classes.keys())
            raise ValueError(
                f"不支持的模型提供商 '{provider}'，支持的有: {supported_providers}")

        # 构造客户端缓存键
        cache_key = f"{provider}:{model_id}"
        if base_url:
            cache_key += f":{base_url}"
        for key, value in sorted(kwargs.items()):
            if isinstance(value, (str, int, float, bool)):
                cache_key += f":{key}={value}"

        # 如果客户端已存在于缓存中，直接返回
        if cache_key in self._clients:
            LOGGER.debug("使用缓存的AI客户端: %s", cache_key)
            return self._clients[cache_key]

        # 创建新客户端实例
        client_class = self.client_classes[provider]
        client_kwargs = {"model": model_id}

        # 添加base_url
        if base_url:
            client_kwargs["base_url"] = base_url

        # 添加其他参数
        client_kwargs.update(kwargs)

        # 创建客户端实例
        client = client_class(**client_kwargs)

        # 缓存客户端实例
        self._clients[cache_key] = client
        LOGGER.info("创建AI客户端: %s (provider=%s, model_id=%s)", cache_key, provider, model_id)

        return client

    async def close_all(self) -> None:
        """关闭所有客户端连接"""
        for key, client in list(self._clients.items()):
            try:
                await client.close()
                LOGGER.info("关闭AI客户端: %s", key)
            except (AttributeError, OSError, RuntimeError) as error:
                LOGGER.error("关闭AI客户端 %s 时出错: %s", key, str(error))

        self._clients.clear()


# 全局AI客户端工厂实例
FACTORY = AIClientFactory()
