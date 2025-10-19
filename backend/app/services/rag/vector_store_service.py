"""向量存储服务（FAISS + BGE-M3）"""

import os
import pickle
from typing import List, Tuple, Optional
from pathlib import Path
import numpy as np
import faiss
from FlagEmbedding import BGEM3FlagModel, FlagReranker
import logging

# 配置 Hugging Face：禁用在线检查，使用本地缓存
os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
os.environ['HF_HUB_OFFLINE'] = '1'  # 强制离线模式
os.environ['TRANSFORMERS_OFFLINE'] = '1'  # Transformers离线模式

logger = logging.getLogger(__name__)


class VectorStoreConfig:
    """向量存储配置"""

    # 使用本地缓存路径（避免网络下载）
    EMBEDDING_MODEL = "/media/HD12T/ztx/.cache/huggingface/models--BAAI--bge-m3/snapshots/5617a9f61b028005a4858fdac845db406aefb181"
    RERANKER_MODEL = "/media/HD12T/ztx/.cache/huggingface/models--BAAI--bge-reranker-v2-m3/snapshots/953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e"
    EMBEDDING_DIM = 1024  # BGE-M3 输出维度
    FAISS_INDEX_PATH = "data/knowledge_base/faiss_indexes"
    USE_FP16 = True  # 使用半精度（节省内存）


class VectorStore:
    """
    向量存储（FAISS + MySQL 混合）

    - FAISS: 快速检索
    - MySQL: 存储向量备份和元数据
    """

    def __init__(self, kb_id: int, config: VectorStoreConfig = None):
        self.kb_id = kb_id
        self.config = config or VectorStoreConfig()

        # FAISS 索引
        self.index: Optional[faiss.Index] = None
        self.chunk_id_mapping: List[int] = []  # FAISS 索引 → chunk_id 映射

        # Embedding 模型（懒加载）
        self._embedder: Optional[BGEM3FlagModel] = None

        # FAISS 文件路径
        self.index_file = self._get_index_path()

    def _get_index_path(self) -> Path:
        """获取 FAISS 索引文件路径"""
        index_dir = Path(self.config.FAISS_INDEX_PATH)
        index_dir.mkdir(parents=True, exist_ok=True)
        return index_dir / f"kb_{self.kb_id}.faiss"

    def _get_mapping_path(self) -> Path:
        """获取 ID 映射文件路径"""
        return self.index_file.with_suffix('.mapping')

    @property
    def embedder(self) -> BGEM3FlagModel:
        """懒加载 Embedding 模型（GPU 加速）"""
        if self._embedder is None:
            logger.info(f"Loading embedding model: {self.config.EMBEDDING_MODEL}")
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")

            self._embedder = BGEM3FlagModel(
                self.config.EMBEDDING_MODEL,
                use_fp16=self.config.USE_FP16,
                device=device  # 明确指定设备
            )
            logger.info(f"Embedding model loaded successfully on {device}")
        return self._embedder

    def initialize_index(self):
        """初始化 FAISS 索引（GPU 可选）"""
        import torch

        # 创建 CPU 索引
        cpu_index = faiss.IndexFlatIP(self.config.EMBEDDING_DIM)

        # 尝试使用 GPU（如果 faiss-gpu 可用）
        gpu_available = False
        if torch.cuda.is_available():
            try:
                # 检查 faiss 是否支持 GPU
                if hasattr(faiss, 'StandardGpuResources'):
                    res = faiss.StandardGpuResources()
                    self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
                    gpu_available = True
                    logger.info(f"✓ Initialized FAISS GPU index for KB {self.kb_id}")
                else:
                    logger.info("FAISS GPU not available, using CPU index")
            except Exception as e:
                logger.info(f"FAISS GPU initialization failed, using CPU: {e}")

        if not gpu_available:
            self.index = cpu_index
            logger.info(f"✓ Initialized FAISS CPU index for KB {self.kb_id}")

        self.chunk_id_mapping = []

    def load_index(self) -> bool:
        """
        从文件加载 FAISS 索引（GPU 可选）

        Returns:
            是否成功加载
        """
        if not self.index_file.exists():
            logger.info(f"Index file not found: {self.index_file}")
            return False

        try:
            import torch

            # 从磁盘加载 CPU 索引
            cpu_index = faiss.read_index(str(self.index_file))

            # 尝试转移到 GPU（如果可用）
            gpu_available = False
            if torch.cuda.is_available() and hasattr(faiss, 'StandardGpuResources'):
                try:
                    res = faiss.StandardGpuResources()
                    self.index = faiss.index_cpu_to_gpu(res, 0, cpu_index)
                    gpu_available = True
                    logger.info(f"✓ Loaded FAISS GPU index: {self.index.ntotal} vectors")
                except Exception as e:
                    logger.info(f"FAISS GPU transfer failed, using CPU: {e}")

            if not gpu_available:
                self.index = cpu_index
                logger.info(f"✓ Loaded FAISS CPU index: {self.index.ntotal} vectors")

            # 加载 ID 映射
            mapping_file = self._get_mapping_path()
            if mapping_file.exists():
                with open(mapping_file, 'rb') as f:
                    self.chunk_id_mapping = pickle.load(f)

            return True

        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False

    def save_index(self):
        """保存 FAISS 索引到文件（GPU 索引先转为 CPU）"""
        if self.index is None:
            logger.warning("No index to save")
            return

        try:
            # 如果是 GPU 索引，转回 CPU
            index_to_save = self.index
            if hasattr(faiss, 'index_gpu_to_cpu'):
                try:
                    index_to_save = faiss.index_gpu_to_cpu(self.index)
                    logger.debug("Converted GPU index to CPU for saving")
                except Exception:
                    # 如果已经是 CPU 索引，会抛出异常，忽略
                    pass

            # 保存 FAISS 索引
            faiss.write_index(index_to_save, str(self.index_file))

            # 保存 ID 映射
            mapping_file = self._get_mapping_path()
            with open(mapping_file, 'wb') as f:
                pickle.dump(self.chunk_id_mapping, f)

            logger.info(f"Saved FAISS index: {self.index.ntotal} vectors")

        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    async def embed_texts(self, texts: List[str]) -> np.ndarray:
        """
        批量生成文本向量

        Returns:
            向量矩阵 (n, 1024)
        """
        if not texts:
            return np.array([])

        # BGE-M3 编码
        embeddings = self.embedder.encode(
            texts,
            batch_size=32,
            max_length=8192  # BGE-M3 支持长文本
        )['dense_vecs']

        # 转换为 numpy array，确保是float32类型（FAISS要求）
        if isinstance(embeddings, list):
            embeddings = np.array(embeddings, dtype=np.float32)
        else:
            embeddings = np.ascontiguousarray(embeddings, dtype=np.float32)

        # 归一化（用于 cosine 相似度）
        faiss.normalize_L2(embeddings)

        return embeddings

    async def add_chunks(
        self,
        chunk_texts: List[str],
        chunk_ids: List[int]
    ):
        """
        添加文档分块到索引

        Args:
            chunk_texts: 分块文本列表
            chunk_ids: 分块 ID 列表
        """
        if len(chunk_texts) != len(chunk_ids):
            raise ValueError("chunk_texts and chunk_ids must have same length")

        if not chunk_texts:
            return

        # 生成向量
        embeddings = await self.embed_texts(chunk_texts)

        # 添加到 FAISS 索引
        if self.index is None:
            self.initialize_index()

        self.index.add(embeddings)
        self.chunk_id_mapping.extend(chunk_ids)

        logger.info(f"Added {len(chunk_texts)} chunks to index")

    async def search(
        self,
        query: str,
        top_k: int = 20,
        threshold: float = 0.7
    ) -> Tuple[List[int], List[float]]:
        """
        向量检索

        Args:
            query: 查询文本
            top_k: 返回结果数量
            threshold: 相似度阈值

        Returns:
            (chunk_ids, scores)
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Empty or uninitialized index")
            return [], []

        # 生成查询向量
        query_embedding = await self.embed_texts([query])

        # FAISS 检索
        scores, indices = self.index.search(query_embedding, top_k)

        # 转换为列表
        scores = scores[0].tolist()
        indices = indices[0].tolist()

        # 过滤低相似度结果
        filtered_results = []
        for idx, score in zip(indices, scores):
            if score >= threshold and 0 <= idx < len(self.chunk_id_mapping):
                chunk_id = self.chunk_id_mapping[idx]
                filtered_results.append((chunk_id, score))

        if not filtered_results:
            return [], []

        chunk_ids, scores = zip(*filtered_results)
        return list(chunk_ids), list(scores)

    def clear_index(self):
        """清空索引"""
        self.initialize_index()
        logger.info(f"Cleared index for KB {self.kb_id}")

    def get_index_size(self) -> int:
        """获取索引大小"""
        if self.index is None:
            return 0
        return self.index.ntotal


class RerankerService:
    """重排序服务"""

    def __init__(self, config: VectorStoreConfig = None):
        self.config = config or VectorStoreConfig()
        self._reranker: Optional[FlagReranker] = None

    @property
    def reranker(self) -> FlagReranker:
        """懒加载 Reranker 模型（GPU 加速）"""
        if self._reranker is None:
            logger.info(f"Loading reranker model: {self.config.RERANKER_MODEL}")
            import torch
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
            logger.info(f"Using device: {device}")

            self._reranker = FlagReranker(
                self.config.RERANKER_MODEL,
                use_fp16=self.config.USE_FP16
            )
            logger.info(f"Reranker model loaded successfully on {device}")
        return self._reranker

    async def rerank(
        self,
        query: str,
        texts: List[str]
    ) -> List[float]:
        """
        重排序

        Args:
            query: 查询文本
            texts: 候选文本列表

        Returns:
            重排序后的分数列表
        """
        if not texts:
            return []

        # 构造 (query, text) 对
        pairs = [(query, text) for text in texts]

        # 计算相关性分数
        scores = self.reranker.compute_score(pairs, batch_size=32)

        # 转换为列表
        if isinstance(scores, (int, float)):
            scores = [scores]
        elif not isinstance(scores, list):
            scores = scores.tolist()

        return scores


def serialize_embedding(embedding: np.ndarray) -> bytes:
    """序列化向量（用于存储到 MySQL）"""
    return pickle.dumps(embedding)


def deserialize_embedding(data: bytes) -> np.ndarray:
    """反序列化向量"""
    return pickle.loads(data)

