"""BGE Embeddings for LangChain"""

import logging
from typing import List
import torch
from transformers import AutoModel, AutoTokenizer
from langchain_core.embeddings import Embeddings

logger = logging.getLogger(__name__)


class BGEEmbeddings(Embeddings):
    """BGE-M3 Embeddings for LangChain

    使用本地 BGE-M3 模型进行文本嵌入，支持 GPU 加速。
    """

    def __init__(
        self,
        model_name: str = "BAAI/bge-m3",
        device: str = None,
        normalize_embeddings: bool = True,
        batch_size: int = 32,
    ):
        """初始化 BGE Embeddings

        Args:
            model_name: 模型路径或名称
            device: 设备 ('cuda' 或 'cpu')，None 则自动检测
            normalize_embeddings: 是否归一化向量
            batch_size: 批处理大小
        """
        self.model_name = model_name
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.normalize_embeddings = normalize_embeddings
        self.batch_size = batch_size

        logger.info(f"加载 BGE-M3 模型: {model_name} on {self.device}")

        # 加载 tokenizer 和 model（强制离线模式）
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            local_files_only=True,
            trust_remote_code=True
        )

        self.model = AutoModel.from_pretrained(
            model_name,
            local_files_only=True,
            trust_remote_code=True
        ).to(self.device)

        self.model.eval()

        logger.info(f"BGE-M3 模型加载成功")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """嵌入多个文档

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        all_embeddings = []

        # 分批处理
        for i in range(0, len(texts), self.batch_size):
            batch_texts = texts[i:i + self.batch_size]
            batch_embeddings = self._embed_batch(batch_texts)
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """嵌入单个查询

        Args:
            text: 查询文本

        Returns:
            向量
        """
        embeddings = self._embed_batch([text])
        return embeddings[0]

    def _embed_batch(self, texts: List[str]) -> List[List[float]]:
        """嵌入一批文本

        Args:
            texts: 文本列表

        Returns:
            向量列表
        """
        # Tokenize
        encoded = self.tokenizer(
            texts,
            max_length=512,
            padding=True,
            truncation=True,
            return_tensors='pt'
        )

        # 移动到设备
        encoded = {k: v.to(self.device) for k, v in encoded.items()}

        # 推理
        with torch.no_grad():
            outputs = self.model(**encoded)
            # 使用 CLS token 作为句子表示
            embeddings = outputs.last_hidden_state[:, 0, :]

            # 归一化
            if self.normalize_embeddings:
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

            # 转换为列表
            embeddings = embeddings.cpu().numpy().tolist()

        return embeddings

