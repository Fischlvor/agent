"""知识库管理服务 - 基于 LangChain + PGVector"""

import os
import shutil
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
import logging
import asyncio

from langchain_community.vectorstores.pgvector import PGVector

from app.models.rag import (
    KnowledgeBase, Document, DocumentChunk, DocumentStatus, ChunkType
)
from app.services.rag.pdf_parser_service import get_pdf_parser
from app.services.rag.model_manager import get_embeddings
from app.core.config import SETTINGS

logger = logging.getLogger(__name__)


def get_ws_manager():
    """延迟导入WebSocket管理器（避免循环导入）"""
    from app.api.endpoints.chat_ws import manager
    return manager


class KnowledgeService:
    """知识库管理服务"""

    def __init__(self, db: Session):
        self.db = db
        self.upload_dir = Path("data/uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        # 使用全局单例的 Embeddings（不会重复加载）
        self.embeddings = get_embeddings()

        # PGVector连接字符串
        self.connection_string = SETTINGS.database_uri

    # ==================== 知识库 CRUD ====================

    def create_knowledge_base(
        self,
        name: str,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> KnowledgeBase:
        """创建知识库"""
        kb = KnowledgeBase(
            name=name,
            description=description,
            config=config or {}
        )
        self.db.add(kb)
        self.db.commit()
        self.db.refresh(kb)

        logger.info(f"Created knowledge base: {kb.name} (ID: {kb.id})")
        return kb

    def get_knowledge_base(self, kb_id: int) -> Optional[KnowledgeBase]:
        """获取知识库"""
        return self.db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_id).first()

    def list_knowledge_bases(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[KnowledgeBase], int]:
        """列出知识库"""
        query = self.db.query(KnowledgeBase)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def update_knowledge_base(
        self,
        kb_id: int,
        name: Optional[str] = None,
        description: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[KnowledgeBase]:
        """更新知识库"""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return None

        if name is not None:
            kb.name = name
        if description is not None:
            kb.description = description
        if config is not None:
            kb.config = config

        self.db.commit()
        self.db.refresh(kb)
        return kb

    def delete_knowledge_base(self, kb_id: int) -> bool:
        """删除知识库（级联删除所有文档和分块）"""
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            return False

        # 删除上传的文件
        kb_upload_dir = self.upload_dir / f"kb_{kb_id}"
        if kb_upload_dir.exists():
            shutil.rmtree(kb_upload_dir)

        # 删除数据库记录（级联删除，包括向量）
        self.db.delete(kb)
        self.db.commit()

        logger.info(f"Deleted knowledge base: {kb_id}")
        return True

    # ==================== 文档管理 ====================

    async def upload_document(
        self,
        kb_id: int,
        file_path: str,
        filename: str
    ) -> Document:
        """
        上传文档

        Returns:
            创建的文档对象（status=pending）
        """
        kb = self.get_knowledge_base(kb_id)
        if not kb:
            raise ValueError(f"Knowledge base {kb_id} not found")

        # 计算文件哈希
        from app.services.rag.pdf_parser_service import PDFParser
        filehash = PDFParser.compute_file_hash(file_path)

        # 检查是否已存在
        existing = self.db.query(Document).filter(
            Document.kb_id == kb_id,
            Document.filehash == filehash
        ).first()

        if existing:
            raise ValueError(f"Document already exists: {existing.filename}")

        # 创建文档记录
        filesize = os.path.getsize(file_path)
        doc = Document(
            kb_id=kb_id,
            filename=filename,
            filepath=file_path,
            filesize=filesize,
            filehash=filehash,
            status=DocumentStatus.PENDING
        )

        self.db.add(doc)
        self.db.commit()
        self.db.refresh(doc)

        logger.info(f"Uploaded document: {filename} (ID: {doc.id})")
        return doc

    async def process_document(self, doc_id: int, user_id: int = None, kb_id: int = None):
        """
        处理文档（解析、分块、向量化）

        这是一个异步任务，应该在后台执行

        Args:
            doc_id: 文档ID
            user_id: 用户ID（用于WebSocket推送）
            kb_id: 知识库ID（用于WebSocket推送）
        """
        doc = self.db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            raise ValueError(f"Document {doc_id} not found")

        try:
            # 更新状态为处理中
            doc.status = DocumentStatus.PROCESSING
            self.db.commit()

            logger.info(f"Processing document {doc_id}: {doc.filename}")

            # 1. 解析 PDF
            parser = get_pdf_parser()
            doc_metadata, chunks = parser.parse_pdf(doc.filepath)

            # 2. 更新文档元数据
            doc.metadata_ = doc_metadata
            doc.page_count = doc_metadata.get('page_count', 0)
            doc.char_count = doc_metadata.get('total_chars', 0)

            # 计数父块和子块
            parent_chunks = [c for c in chunks if c.chunk_type == 'parent']
            child_chunks = [c for c in chunks if c.chunk_type == 'child']

            doc.parent_chunk_count = len(parent_chunks)
            doc.chunk_count = len(child_chunks)

            # 3. 删除旧的chunks（如果文档重新处理）
            self.db.query(DocumentChunk).filter(
                DocumentChunk.doc_id == doc.id
            ).delete()
            self.db.flush()

            logger.info(f"开始处理 {len(chunks)} 个分块...")

            # 4. 插入父块和子块到数据库
            chunk_id_map = {}  # parent_index -> db_id

            for chunk in chunks:
                if chunk.chunk_type == 'parent':
                    # 插入父块（不需要embedding）
                    db_chunk = DocumentChunk(
                        doc_id=doc.id,
                        parent_id=None,
                        content=chunk.content,
                        chunk_index=chunk.chunk_index,
                        chunk_type=ChunkType.PARENT,
                        embedding=None,
                        embedding_model=None,
                        page_number=chunk.page_number,
                        token_count=chunk.token_count,
                        char_count=chunk.char_count,
                        metadata_=chunk.metadata
                    )
                    self.db.add(db_chunk)
                    self.db.flush()

                    # 保存 parent_index -> db_id 映射
                    chunk_id_map[chunk.chunk_index] = db_chunk.id

            # 5. 为子块生成向量
            logger.info(f"生成 {len(child_chunks)} 个子块的向量...")
            child_texts = [c.content for c in child_chunks]
            child_embeddings = self.embeddings.embed_documents(child_texts)

            # 6. 插入子块（带向量）
            for chunk, embedding in zip(child_chunks, child_embeddings):
                parent_db_id = chunk_id_map.get(chunk.parent_id)

                db_chunk = DocumentChunk(
                    doc_id=doc.id,
                    parent_id=parent_db_id,
                    content=chunk.content,
                    chunk_index=chunk.chunk_index,
                    chunk_type=ChunkType.CHILD,
                    embedding=embedding,  # pgvector.sqlalchemy.Vector 会自动处理
                    embedding_model="BAAI/bge-m3",
                    page_number=chunk.page_number,
                    token_count=chunk.token_count,
                    char_count=chunk.char_count,
                    metadata_=chunk.metadata
                )
                self.db.add(db_chunk)

            # 7. 提交所有chunks
            self.db.flush()

            # 8. 更新文档状态
            doc.status = DocumentStatus.COMPLETED
            doc.processed_at = datetime.now()

            # 9. 更新知识库统计
            kb = self.get_knowledge_base(doc.kb_id)
            kb.doc_count = self.db.query(Document).filter(
                Document.kb_id == doc.kb_id
            ).count()
            kb.chunk_count = self.db.query(DocumentChunk).join(Document).filter(
                Document.kb_id == doc.kb_id,
                DocumentChunk.chunk_type == ChunkType.CHILD
            ).count()

            self.db.commit()

            logger.info(f"✓ Document {doc_id} processed successfully!")

            # WebSocket推送：处理完成
            if user_id and kb_id:
                try:
                    manager = get_ws_manager()
                    await manager.notify_document_status(
                        user_id=str(user_id),
                        kb_id=kb_id,
                        doc_id=doc_id,
                        status='completed'
                    )
                except Exception as ws_err:
                    logger.warning(f"WebSocket通知失败: {ws_err}")

        except Exception as e:
            logger.error(f"Document processing failed: {e}", exc_info=True)
            doc.status = DocumentStatus.FAILED
            doc.error_msg = str(e)
            self.db.commit()

            # WebSocket推送：处理失败
            if user_id and kb_id:
                try:
                    manager = get_ws_manager()
                    await manager.notify_document_status(
                        user_id=str(user_id),
                        kb_id=kb_id,
                        doc_id=doc_id,
                        status='failed',
                        error_msg=str(e)
                    )
                except Exception as ws_err:
                    logger.warning(f"WebSocket通知失败: {ws_err}")

            raise

    def get_document(self, doc_id: int) -> Optional[Document]:
        """获取文档"""
        return self.db.query(Document).filter(Document.id == doc_id).first()

    def list_documents(
        self,
        kb_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Document], int]:
        """列出知识库的文档"""
        query = self.db.query(Document).filter(Document.kb_id == kb_id)
        total = query.count()
        items = query.offset(skip).limit(limit).all()
        return items, total

    def delete_document(self, doc_id: int) -> bool:
        """删除文档（级联删除所有分块和向量）"""
        doc = self.get_document(doc_id)
        if not doc:
            return False

        kb_id = doc.kb_id  # 保存知识库ID，因为删除后doc对象会失效

        # 删除文件
        if os.path.exists(doc.filepath):
            os.remove(doc.filepath)

        # 删除数据库记录（级联删除chunks和向量）
        self.db.delete(doc)
        self.db.commit()

        # 更新知识库统计
        kb = self.get_knowledge_base(kb_id)
        if kb:
            kb.doc_count = self.db.query(Document).filter(
                Document.kb_id == kb_id
            ).count()
            kb.chunk_count = self.db.query(DocumentChunk).join(Document).filter(
                Document.kb_id == kb_id,
                DocumentChunk.chunk_type == ChunkType.CHILD
            ).count()
            self.db.commit()

        logger.info(f"Deleted document: {doc_id}")
        return True
