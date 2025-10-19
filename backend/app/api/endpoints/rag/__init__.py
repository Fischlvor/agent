"""RAG API 端点"""

from fastapi import APIRouter
from app.api.endpoints.rag import knowledge_bases, documents

# 创建 RAG 路由
rag_router = APIRouter()

# 注册子路由
rag_router.include_router(
    knowledge_bases.router,
    prefix="/knowledge-bases",
    tags=["knowledge-bases"]
)

rag_router.include_router(
    documents.router,
    prefix="/knowledge-bases",
    tags=["documents"]
)

__all__ = ["rag_router"]





