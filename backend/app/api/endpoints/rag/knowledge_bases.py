"""知识库管理 API"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.services.rag import KnowledgeService
from app.schemas.rag import (
    KnowledgeBaseCreate,
    KnowledgeBaseUpdate,
    KnowledgeBaseResponse,
    KnowledgeBaseList,
)

router = APIRouter()


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
def create_knowledge_base(
    kb_data: KnowledgeBaseCreate,
    db: Session = Depends(get_db)
):
    """创建知识库"""
    service = KnowledgeService(db)
    kb = service.create_knowledge_base(
        name=kb_data.name,
        description=kb_data.description,
        config=kb_data.config
    )
    return kb


@router.get("", response_model=KnowledgeBaseList)
def list_knowledge_bases(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """列出所有知识库"""
    service = KnowledgeService(db)
    items, total = service.list_knowledge_bases(skip=skip, limit=limit)
    return KnowledgeBaseList(items=items, total=total)


@router.get("/{kb_id}", response_model=KnowledgeBaseResponse)
def get_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """获取知识库详情"""
    service = KnowledgeService(db)
    kb = service.get_knowledge_base(kb_id)
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found"
        )
    return kb


@router.put("/{kb_id}", response_model=KnowledgeBaseResponse)
def update_knowledge_base(
    kb_id: int,
    kb_data: KnowledgeBaseUpdate,
    db: Session = Depends(get_db)
):
    """更新知识库"""
    service = KnowledgeService(db)
    kb = service.update_knowledge_base(
        kb_id=kb_id,
        name=kb_data.name,
        description=kb_data.description,
        config=kb_data.config
    )
    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found"
        )
    return kb


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_knowledge_base(
    kb_id: int,
    db: Session = Depends(get_db)
):
    """删除知识库"""
    service = KnowledgeService(db)
    success = service.delete_knowledge_base(kb_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge base {kb_id} not found"
        )
    return None


