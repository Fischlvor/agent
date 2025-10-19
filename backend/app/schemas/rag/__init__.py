"""RAG 相关 Schemas"""

from app.schemas.rag.knowledge import (
    # 知识库
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseList,
    # 文档
    DocumentMetadata,
    DocumentUploadResponse,
    DocumentResponse,
    DocumentList,
    DocumentProcessStatus,
    # 检索
    RetrievalRequest,
    MatchedChild,
    RetrievalResult,
    RetrievalResponse,
    # 调试
    ChunkInfo,
    ParentChunkInfo,
    DocumentChunksResponse,
)

__all__ = [
    # 知识库
    "KnowledgeBaseCreate",
    "KnowledgeBaseUpdate",
    "KnowledgeBaseResponse",
    "KnowledgeBaseList",
    # 文档
    "DocumentMetadata",
    "DocumentUploadResponse",
    "DocumentResponse",
    "DocumentList",
    "DocumentProcessStatus",
    # 检索
    "RetrievalRequest",
    "MatchedChild",
    "RetrievalResult",
    "RetrievalResponse",
    # 调试
    "ChunkInfo",
    "ParentChunkInfo",
    "DocumentChunksResponse",
]

