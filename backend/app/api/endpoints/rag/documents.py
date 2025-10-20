"""文档管理和检索 API"""

import asyncio
import logging
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

from app.db import get_db
from app.db.session import SESSION_LOCAL
from app.models.user import User
from app.models.rag import DocumentStatus
from app.middleware.auth import get_current_user
from app.services.rag import KnowledgeService, RetrievalService
from app.schemas.rag import (
    DocumentUploadResponse,
    DocumentResponse,
    DocumentList,
    RetrievalRequest,
    RetrievalResponse,
)

router = APIRouter()

# 用于执行后台任务的线程池
_executor = ThreadPoolExecutor(max_workers=4)


def _run_async_in_thread(doc_id: int, user_id: int, kb_id: int):
    """在独立线程的新事件循环中执行异步任务

    Args:
        doc_id: 文档ID
        user_id: 用户ID
        kb_id: 知识库ID
    """
    async def _async_process():
        db = SESSION_LOCAL()
        try:
            service = KnowledgeService(db)
            await service.process_document(doc_id, user_id, kb_id)
        except Exception as e:
            logger.error("后台文档处理失败: doc_id=%s, error=%s", doc_id, str(e), exc_info=True)
        finally:
            db.close()

    # 在新的事件循环中运行异步任务
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(_async_process())
    finally:
        loop.close()


def _process_document_background(doc_id: int, user_id: int, kb_id: int):
    """后台任务包装函数：在线程池中执行文档处理

    Args:
        doc_id: 文档ID
        user_id: 用户ID
        kb_id: 知识库ID
    """
    # 提交到线程池异步执行，不等待结果
    _executor.submit(_run_async_in_thread, doc_id, user_id, kb_id)


@router.post("/{kb_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: int,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    上传文档

    支持的文件类型：PDF
    """
    # 验证文件类型
    if not file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF files are supported"
        )

    # 验证知识库存在
    service = KnowledgeService(db)
    kb = service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found"
        )

    # 保存上传的文件
    upload_dir = Path("data/uploads") / f"kb_{kb_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    file_path = upload_dir / file.filename

    try:
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 创建文档记录（状态：PENDING）
        doc = await service.upload_document(
            kb_id=kb_id,
            file_path=str(file_path),
            filename=file.filename
        )

        # 立即更新为 PROCESSING 状态
        doc.status = DocumentStatus.PROCESSING
        db.commit()
        db.refresh(doc)

        # 推送 PROCESSING 状态到前端（通过 WebSocket）
        from app.api.endpoints.chat_ws import manager
        try:
            await manager.notify_document_status(
                user_id=str(current_user.id),
                kb_id=kb_id,
                doc_id=doc.id,
                status='processing'
            )
            logger.info("推送 PROCESSING 状态: doc_id=%s, user_id=%s", doc.id, current_user.id)
        except Exception:  # noqa: S110
            # WebSocket 推送失败不影响主流程（用户可能未连接 WebSocket）
            logger.debug("WebSocket 推送失败（用户可能未连接）: doc_id=%s", doc.id)

        # 添加后台处理任务（解析、分块、向量化）
        # ✅ 使用独立的数据库 session，避免与主请求的 session 冲突
        background_tasks.add_task(_process_document_background, doc.id, current_user.id, kb_id)

        return DocumentUploadResponse(
            doc_id=doc.id,
            filename=doc.filename,
            status=doc.status.value,
            message="Document uploaded successfully. Processing in background."
        )

    except ValueError as e:
        # 文件已存在等业务错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e
    except Exception as e:
        # 清理失败的文件
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        ) from e


@router.get("/{kb_id}/documents", response_model=DocumentList)
def list_documents(
    kb_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """列出知识库中的所有文档"""
    service = KnowledgeService(db)
    items, total = service.list_documents(kb_id=kb_id, skip=skip, limit=limit)
    return DocumentList(items=items, total=total)


@router.get("/documents/{doc_id}", response_model=DocumentResponse)
def get_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """获取文档详情"""
    service = KnowledgeService(db)
    doc = service.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    return doc


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    db: Session = Depends(get_db)
):
    """删除文档"""
    service = KnowledgeService(db)
    success = service.delete_document(doc_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found"
        )
    return None


@router.post("/{kb_id}/retrieve", response_model=RetrievalResponse)
async def retrieve(
    kb_id: int,
    request: RetrievalRequest,
    db: Session = Depends(get_db)
):
    """
    检索知识库

    使用两阶段检索：
    1. 向量召回（Top-K 子块）
    2. 重排序 + 去重（返回父块）
    """
    # 验证知识库存在
    kb_service = KnowledgeService(db)
    kb = kb_service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found"
        )

    # 检索
    retrieval_service = RetrievalService(db)
    results, search_time = await retrieval_service.retrieve(
        query=request.query,
        kb_id=kb_id,
        top_k=request.top_k,
        top_k_recall=20,  # 召回 20 个子块
        similarity_threshold=request.similarity_threshold,
        use_rerank=request.use_rerank
    )

    return RetrievalResponse(
        query=request.query,
        results=results,
        total_found=len(results),
        search_time_ms=search_time
    )


