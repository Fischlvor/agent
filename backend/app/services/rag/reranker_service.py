"""Reranker服务 - BGE-Reranker-V2-M3"""

import logging
import os
from typing import List
import torch
from FlagEmbedding import FlagReranker

logger = logging.getLogger(__name__)


class RerankerService:
    """Reranker服务 - 使用 BGE-Reranker-V2-M3"""

    def __init__(
        self,
        model_path: str = "BAAI/bge-reranker-v2-m3"
    ):
        """初始化 Reranker

        Args:
            model_path: 模型路径
        """
        self.model_path = model_path
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'

        logger.info(f"加载 BGE-Reranker-V2-M3: {model_path} on {self.device}")

        # 强制离线模式
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'

        # 加载 Reranker 模型
        self.reranker = FlagReranker(
            model_path,
            use_fp16=True if self.device == 'cuda' else False
        )

        logger.info(f"BGE-Reranker-V2-M3 加载成功")

    async def rerank(
        self,
        query: str,
        texts: List[str],
        normalize: bool = True
    ) -> List[float]:
        """重排序文本列表

        Args:
            query: 查询文本
            texts: 候选文本列表
            normalize: 是否归一化分数到 [0, 1]（注：目前FlagReranker不支持此参数，已移除）

        Returns:
            重排分数列表
        """
        if not texts:
            return []

        # 构造输入对
        pairs = [[query, text] for text in texts]

        # 计算分数（FlagReranker不支持normalize参数）
        scores = self.reranker.compute_score(pairs)

        # 确保返回列表
        if isinstance(scores, float):
            scores = [scores]

        return scores

