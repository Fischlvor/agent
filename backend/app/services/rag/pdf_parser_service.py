"""
PDF解析服务 - 使用 LangChain PyMuPDFLoader + 父子分块策略
"""

import os
import hashlib
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, field

from langchain_community.document_loaders import PyMuPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)


@dataclass
class ChunkData:
    """分块数据"""
    content: str
    chunk_index: int
    chunk_type: str  # "parent" or "child"
    parent_id: int = None  # 父块的索引（对于child chunk）
    page_number: int = None
    token_count: int = 0
    char_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PDFParserConfig:
    """PDF解析配置"""

    # Tokenizer（用于计算token数）
    TOKENIZER_MODEL = "BAAI/bge-m3"  # 使用模型名，从本地缓存加载

    # 父块配置（粗粒度，用于上下文）
    PARENT_CHUNK_SIZE = 2048  # tokens
    PARENT_CHUNK_OVERLAP = 256  # tokens

    # 子块配置（细粒度，用于检索）
    CHILD_CHUNK_SIZE = 512  # tokens
    CHILD_CHUNK_OVERLAP = 64  # tokens

    # 分隔符优先级（LangChain）
    SEPARATORS = [
        "\n\n\n",  # 多空行
        "\n\n",    # 段落
        "\n",      # 单行
        "。",      # 中文句号
        ".",       # 英文句号
        "！",      # 中文感叹号
        "!",       # 英文感叹号
        "？",      # 中文问号
        "?",       # 英文问号
        "；",      # 中文分号
        ";",       # 英文分号
        " ",       # 空格
        "",        # 字符级别
    ]


class PDFParser:
    """PDF解析器 - 基于 LangChain"""

    def __init__(self):
        """初始化解析器"""
        # 加载tokenizer（离线模式）
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(
                PDFParserConfig.TOKENIZER_MODEL,
                local_files_only=True,
                trust_remote_code=True
            )
            logger.info(f"✓ Tokenizer加载成功: {PDFParserConfig.TOKENIZER_MODEL}")
        except Exception as e:
            logger.error(f"Tokenizer加载失败: {e}")
            raise

        # 创建LangChain分块器（父块）
        self.parent_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=self.tokenizer,
            chunk_size=PDFParserConfig.PARENT_CHUNK_SIZE,
            chunk_overlap=PDFParserConfig.PARENT_CHUNK_OVERLAP,
            separators=PDFParserConfig.SEPARATORS,
            keep_separator=True,
        )

        # 创建LangChain分块器（子块）
        self.child_splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
            tokenizer=self.tokenizer,
            chunk_size=PDFParserConfig.CHILD_CHUNK_SIZE,
            chunk_overlap=PDFParserConfig.CHILD_CHUNK_OVERLAP,
            separators=PDFParserConfig.SEPARATORS,
            keep_separator=True,
        )

    @staticmethod
    def compute_file_hash(filepath: str) -> str:
        """计算文件SHA256哈希"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def parse_pdf(self, filepath: str) -> Tuple[Dict[str, Any], List[ChunkData]]:
        """
        解析PDF文件，返回元数据和分块数据

        Args:
            filepath: PDF文件路径

        Returns:
            (文档元数据, 分块列表)
        """
        logger.info(f"开始解析PDF: {filepath}")

        # 1. 使用 LangChain PyMuPDFLoader 加载文档
        loader = PyMuPDFLoader(filepath)
        documents = loader.load()

        logger.info(f"✓ PyMuPDFLoader加载完成: {len(documents)}页")

        # 2. 提取元数据
        doc_metadata = self._extract_metadata(documents, filepath)

        # 3. 构建页码映射（page_number -> document_index）
        page_map = {}
        for idx, doc in enumerate(documents):
            page_num = doc.metadata.get("page", idx + 1)
            page_map[idx] = page_num

        # 4. 父子分块
        chunks = self._chunk_documents(documents, page_map)

        logger.info(f"✓ 分块完成: {len([c for c in chunks if c.chunk_type == 'parent'])}个父块, "
                   f"{len([c for c in chunks if c.chunk_type == 'child'])}个子块")

        return doc_metadata, chunks

    def _extract_metadata(self, documents: List[Any], filepath: str) -> Dict[str, Any]:
        """从 LangChain documents 中提取元数据"""
        if not documents:
            return {}

        # 获取第一页的元数据（通常包含文档级元数据）
        first_doc = documents[0]
        metadata = first_doc.metadata.copy()

        # 添加文档统计信息
        metadata.update({
            "page_count": len(documents),
            "total_chars": sum(len(doc.page_content) for doc in documents),
            "filename": os.path.basename(filepath),
        })

        return metadata

    def _chunk_documents(self, documents: List[Any], page_map: Dict[int, int]) -> List[ChunkData]:
        """
        对文档进行父子分块

        Args:
            documents: LangChain Document 列表
            page_map: 索引到页码的映射

        Returns:
            ChunkData 列表
        """
        all_chunks = []
        parent_index = 0
        child_index = 0

        # 合并所有页面文本（保留页码信息）
        for doc_idx, doc in enumerate(documents):
            page_num = page_map.get(doc_idx, doc_idx + 1)
            text = doc.page_content

            if not text.strip():
                continue

            # 1. 父块分割
            parent_texts = self.parent_splitter.split_text(text)

            for parent_text in parent_texts:
                if not parent_text.strip():
                    continue

                # 创建父块
                parent_chunk = ChunkData(
                    content=parent_text,
                    chunk_index=parent_index,
                    chunk_type="parent",
                    page_number=page_num,
                    token_count=len(self.tokenizer.encode(parent_text)),
                    char_count=len(parent_text),
                    metadata={
                        "source": "pdf",
                        "page": page_num,
                    }
                )
                all_chunks.append(parent_chunk)

                # 2. 子块分割（从父块中分割）
                child_texts = self.child_splitter.split_text(parent_text)

                for child_text in child_texts:
                    if not child_text.strip():
                        continue

                    child_chunk = ChunkData(
                        content=child_text,
                        chunk_index=child_index,
                        chunk_type="child",
                        parent_id=parent_index,  # 关联到父块
                        page_number=page_num,
                        token_count=len(self.tokenizer.encode(child_text)),
                        char_count=len(child_text),
                        metadata={
                            "source": "pdf",
                            "page": page_num,
                            "parent_index": parent_index,
                        }
                    )
                    all_chunks.append(child_chunk)
                    child_index += 1

                parent_index += 1

        return all_chunks

    def parse_and_validate(self, filepath: str) -> Tuple[bool, str, Dict[str, Any], List[ChunkData]]:
        """
        解析PDF并验证

        Returns:
            (是否成功, 错误信息, 文档元数据, 分块列表)
        """
        try:
            if not os.path.exists(filepath):
                return False, f"文件不存在: {filepath}", {}, []

            if not filepath.lower().endswith('.pdf'):
                return False, "只支持PDF文件", {}, []

            doc_metadata, chunks = self.parse_pdf(filepath)

            if not chunks:
                return False, "未能提取到有效内容", doc_metadata, []

            return True, "", doc_metadata, chunks

        except Exception as e:
            logger.error(f"PDF解析失败: {e}", exc_info=True)
            return False, f"PDF解析失败: {str(e)}", {}, []


# 单例实例
_parser_instance = None

def get_pdf_parser() -> PDFParser:
    """获取PDF解析器单例"""
    global _parser_instance
    if _parser_instance is None:
        _parser_instance = PDFParser()
    return _parser_instance
