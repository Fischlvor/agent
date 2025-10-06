"""API路由配置模块"""

from fastapi import APIRouter

from app.api.endpoints import admin, auth, chat, chat_ws, users

# 创建API路由器
api_router = APIRouter()

# 注册各个端点
api_router.include_router(auth.router)  # SSO认证服务
api_router.include_router(users.router)  # 用户资源管理
api_router.include_router(admin.router)  # 管理员功能
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])  # 聊天管理
api_router.include_router(chat_ws.router, tags=["chat-websocket"])  # WebSocket聊天

