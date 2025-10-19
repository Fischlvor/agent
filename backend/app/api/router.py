"""API路由配置模块"""

from fastapi import APIRouter

from app.api.endpoints import admin, analytics, auth, chat, chat_ws, users
from app.api.endpoints.rag import rag_router

# 创建API路由器
api_router = APIRouter()

# 注册各个端点
api_router.include_router(auth.router)  # SSO认证服务
api_router.include_router(users.router)  # 用户资源管理
api_router.include_router(admin.router)  # 管理员功能
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])  # 聊天管理
api_router.include_router(chat_ws.router, tags=["chat-websocket"])  # WebSocket聊天
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])  # 分析统计
api_router.include_router(rag_router, prefix="/rag", tags=["rag"])  # RAG 知识库

