"""RAG 模型管理器 - 单例模式"""

import logging
from typing import Optional

from app.services.rag.bge_embeddings import BGEEmbeddings
from app.services.rag.reranker_service import RerankerService

logger = logging.getLogger(__name__)


class ModelManager:
    """模型管理器单例"""

    _instance: Optional['ModelManager'] = None
    _embeddings: Optional[BGEEmbeddings] = None
    _reranker: Optional[RerankerService] = None
    _initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self):
        """初始化模型（只执行一次）"""
        if self._initialized:
            logger.info("模型已初始化，跳过")
            return

        logger.info("开始初始化 RAG 模型...")

        # 初始化 Embeddings
        logger.info("加载 BGE-M3 Embeddings...")
        self._embeddings = BGEEmbeddings(model_name="BAAI/bge-m3")
        logger.info("✓ BGE-M3 Embeddings 加载完成")

        # 初始化 Reranker
        logger.info("加载 BGE-Reranker-V2-M3...")
        self._reranker = RerankerService(model_path="BAAI/bge-reranker-v2-m3")
        logger.info("✓ BGE-Reranker-V2-M3 加载完成")

        self._initialized = True
        logger.info("✅ RAG 模型初始化完成")

    @property
    def embeddings(self) -> BGEEmbeddings:
        """获取 Embeddings 实例"""
        if not self._initialized or self._embeddings is None:
            raise RuntimeError("模型未初始化，请先调用 initialize()")
        return self._embeddings

    @property
    def reranker(self) -> RerankerService:
        """获取 Reranker 实例"""
        if not self._initialized or self._reranker is None:
            raise RuntimeError("模型未初始化，请先调用 initialize()")
        return self._reranker

    @property
    def is_initialized(self) -> bool:
        """检查是否已初始化"""
        return self._initialized


# 全局实例
_model_manager = ModelManager()


def get_model_manager() -> ModelManager:
    """获取模型管理器实例"""
    return _model_manager


def get_embeddings() -> BGEEmbeddings:
    """获取 Embeddings 实例（便捷方法）"""
    return _model_manager.embeddings


def get_reranker() -> RerankerService:
    """获取 Reranker 实例（便捷方法）"""
    return _model_manager.reranker

