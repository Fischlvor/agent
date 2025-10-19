"""文档管理和检索 API"""

import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.user import User
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


@router.post("/{kb_id}/upload", response_model=DocumentUploadResponse)
async def upload_document(
    kb_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
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

        # 创建文档记录
        doc = await service.upload_document(
            kb_id=kb_id,
            file_path=str(file_path),
            filename=file.filename
        )

        # 后台处理文档（解析、分块、向量化）
        if background_tasks:
            background_tasks.add_task(service.process_document, doc.id, current_user.id, kb_id)

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


