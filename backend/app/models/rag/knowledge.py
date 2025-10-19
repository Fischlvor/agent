"""知识库相关模型"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, BigInteger, DateTime, ForeignKey, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector
import enum

from app.models.base import BaseModel


class DocumentStatus(enum.Enum):
    """文档处理状态"""
    PENDING = "pending"          # 待处理
    PROCESSING = "processing"    # 处理中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败


class ChunkType(enum.Enum):
    """块类型"""
    PARENT = "parent"   # 父块（粗粒度，用于上下文）
    CHILD = "child"     # 子块（细粒度，用于检索）


class KnowledgeBase(BaseModel):
    """知识库模型"""

    __tablename__ = "knowledge_bases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, comment="知识库名称")
    description = Column(Text, comment="知识库描述")

    # 配置信息（JSONB）
    config = Column(JSONB, comment="配置信息：分块参数、模型设置等")

    # 统计信息
    doc_count = Column(Integer, default=0, comment="文档数量")
    chunk_count = Column(Integer, default=0, comment="分块总数")

    # 关系
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_kb_name", "name"),
    )


class Document(BaseModel):
    """文档模型"""

    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    kb_id = Column(Integer, ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment="所属知识库")

    # 文件信息
    filename = Column(String(255), nullable=False, comment="文件名")
    filepath = Column(String(500), nullable=False, comment="文件路径")
    filesize = Column(BigInteger, comment="文件大小（字节）")
    filehash = Column(String(64), comment="文件SHA256哈希")
    mimetype = Column(String(100), default="application/pdf", comment="文件类型")

    # 元数据（JSONB存储）
    # 注意：metadata 是 SQLAlchemy 保留字，使用 metadata_ 作为属性名
    metadata_ = Column("metadata", JSONB, comment="文档元数据：标题、作者、摘要等")
    """
    metadata 结构示例：
    {
        "title": "论文标题",
        "authors": ["作者1", "作者2"],
        "abstract": "摘要内容",
        "keywords": ["关键词1", "关键词2"],
        "publish_date": "2024-01-01",
        "doi": "10.xxxx/xxxx",
        "language": "en"
    }
    """

    # 处理状态
    status = Column(
        SQLEnum(DocumentStatus),
        default=DocumentStatus.PENDING,
        nullable=False,
        comment="处理状态"
    )
    error_msg = Column(Text, comment="错误信息")

    # 统计信息
    page_count = Column(Integer, comment="页数")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    parent_chunk_count = Column(Integer, default=0, comment="父块数量")
    char_count = Column(Integer, comment="字符总数")

    processed_at = Column(DateTime, comment="处理完成时间")

    # 关系
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_doc_kb_id", "kb_id"),
        Index("idx_doc_status", "status"),
        Index("idx_doc_kb_hash", "kb_id", "filehash", unique=True),  # 同一知识库不允许重复上传
    )


class DocumentChunk(BaseModel):
    """文档块模型（统一父子块）"""

    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="所属文档ID")
    parent_id = Column(Integer, ForeignKey("document_chunks.id", ondelete="CASCADE"), nullable=True, comment="父块ID（NULL表示是parent chunk）")

    # 块内容
    content = Column(Text, nullable=False, comment="块内容")
    chunk_index = Column(Integer, nullable=False, comment="块序号")
    chunk_type = Column(
        SQLEnum(ChunkType),
        nullable=False,
        comment="块类型"
    )

    # Embedding相关（只有child chunk有）
    # 使用 pgvector 的 Vector 类型，1024 维度对应 BGE-M3
    embedding = Column(Vector(1024), nullable=True, comment="向量表示")
    embedding_model = Column(String(100), nullable=True, comment="Embedding模型")

    # 位置信息
    page_number = Column(Integer, nullable=True, comment="页码（PDF特有）")
    section_title = Column(String(500), nullable=True, comment="所在章节")

    # 统计信息
    token_count = Column(Integer, nullable=True, comment="Token数量")
    char_count = Column(Integer, nullable=True, comment="字符数量")

    # 元数据
    # 注意：metadata 是 SQLAlchemy 保留字，使用 metadata_ 作为属性名
    metadata_ = Column("metadata", JSONB, nullable=True, comment="扩展元数据")
    """
    metadata 结构示例（PDF）：
    {
        "bbox": [x0, y0, x1, y1],  # 边界框坐标
        "section": "Introduction",  # 章节名称
        "source_type": "pdf",       # 来源类型
        "has_citation": true,       # 是否包含引用
        "has_equation": false,      # 是否包含公式
        "has_figure_ref": true      # 是否包含图表引用
    }
    """

    # 关系
    document = relationship("Document", back_populates="chunks")
    parent = relationship("DocumentChunk", remote_side=[id], backref="children")

    __table_args__ = (
        Index("idx_document_chunks_doc_id", "doc_id"),
        Index("idx_document_chunks_parent_id", "parent_id"),
        Index("idx_document_chunks_type", "chunk_type"),
        Index("idx_document_chunks_page", "page_number"),
        Index("idx_document_chunks_unique", "doc_id", "chunk_type", "chunk_index", unique=True),
    )
