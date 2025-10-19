"""知识库相关 Schema"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ==================== 知识库 ====================

class KnowledgeBaseCreate(BaseModel):
    """创建知识库请求"""
    name: str = Field(..., min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="配置信息")


class KnowledgeBaseUpdate(BaseModel):
    """更新知识库请求"""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="知识库名称")
    description: Optional[str] = Field(None, description="知识库描述")
    config: Optional[Dict[str, Any]] = Field(None, description="配置信息")


class KnowledgeBaseResponse(BaseModel):
    """知识库响应"""
    id: int
    name: str
    description: Optional[str]
    config: Optional[Dict[str, Any]]
    doc_count: int
    chunk_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeBaseList(BaseModel):
    """知识库列表响应"""
    items: List[KnowledgeBaseResponse]
    total: int


# ==================== 文档 ====================

class DocumentMetadata(BaseModel):
    """文档元数据"""
    title: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publish_date: Optional[str] = None
    doi: Optional[str] = None
    language: Optional[str] = "en"


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    doc_id: int
    filename: str
    status: str
    message: str


class DocumentResponse(BaseModel):
    """文档响应"""
    id: int
    kb_id: int
    filename: str
    filepath: str
    filesize: Optional[int]
    filehash: Optional[str]
    mimetype: str
    metadata: Optional[Dict[str, Any]] = Field(None, validation_alias='metadata_')
    status: str
    error_msg: Optional[str]
    page_count: Optional[int]
    chunk_count: int
    parent_chunk_count: int
    char_count: Optional[int]
    processed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class DocumentList(BaseModel):
    """文档列表响应"""
    items: List[DocumentResponse]
    total: int


class DocumentProcessStatus(BaseModel):
    """文档处理状态"""
    doc_id: int
    status: str
    progress: float = Field(..., ge=0, le=1, description="处理进度 0-1")
    message: Optional[str] = None
    error: Optional[str] = None


# ==================== 检索 ====================

class RetrievalRequest(BaseModel):
    """检索请求"""
    query: str = Field(..., min_length=1, description="查询文本")
    kb_id: int = Field(..., description="知识库ID")
    top_k: int = Field(5, ge=1, le=20, description="返回结果数量")
    similarity_threshold: float = Field(0.7, ge=0, le=1, description="相似度阈值")
    use_rerank: bool = Field(True, description="是否使用重排序")


class MatchedChild(BaseModel):
    """匹配的子块信息"""
    child_id: int
    child_text: str
    score: float
    chunk_index: int


class RetrievalResult(BaseModel):
    """单个检索结果"""
    parent_id: int
    parent_text: str
    doc_id: int
    doc_title: Optional[str]
    section: Optional[str]
    page_number: Optional[int]
    matched_children: List[MatchedChild]
    max_score: float
    source: str = Field(..., description="来源文件名")


class RetrievalResponse(BaseModel):
    """检索响应"""
    query: str
    results: List[RetrievalResult]
    total_found: int
    search_time_ms: int = Field(..., description="检索耗时（毫秒）")


# ==================== 分块信息 ====================

class ChunkInfo(BaseModel):
    """分块信息（调试用）"""
    chunk_id: int
    chunk_text: str
    parent_id: int
    token_count: Optional[int]
    metadata: Optional[Dict[str, Any]]


class ParentChunkInfo(BaseModel):
    """父块信息（调试用）"""
    parent_id: int
    parent_text: str
    parent_index: int
    child_count: int
    section: Optional[str]
    page_number: Optional[int]


class DocumentChunksResponse(BaseModel):
    """文档分块响应（调试用）"""
    doc_id: int
    filename: str
    parent_chunks: List[ParentChunkInfo]
    total_parents: int
    total_children: int

