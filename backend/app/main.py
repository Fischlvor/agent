"""主应用模块，定义FastAPI应用实例和配置。"""

import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import SETTINGS
from app.core.redis_client import redis_service
from app.middleware.rate_limit import RateLimitMiddleware

# ============ 配置日志 ============
# 配置根日志记录器，确保应用程序的日志也能输出
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

# 确保应用程序模块的日志输出
logging.getLogger("app").setLevel(logging.INFO)

# 创建FastAPI应用
APP = FastAPI(
    title=SETTINGS.project_name,
    description=SETTINGS.project_description,
    openapi_url=f"{SETTINGS.api_v1_str}/openapi.json",
)

# 配置CORS
APP.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ 添加频率限制中间件（每分钟最多60次请求）
APP.add_middleware(
    RateLimitMiddleware,
    max_requests=60,
    window_seconds=60,
    exclude_paths=[
        "/api/v1/auth/login",
        "/api/v1/auth/send-code",
        "/api/v1/health",
        "/health",
        "/docs",
        "/openapi.json",
        "/api/v1/chat/ws"  # WebSocket 不限流
    ]
)

# 注册API路由
APP.include_router(api_router, prefix=SETTINGS.api_v1_str)


# 启动事件
@APP.on_event("startup")
async def startup_event():
    """应用启动时的事件处理函数。"""
    print(f"Starting {SETTINGS.project_name}...")
    print(f"Database: {SETTINGS.database_type}")
    print(f"Database URI: {SETTINGS.database_uri}")

    # 测试Redis连接
    if redis_service.ping():
        print("✓ Redis连接成功")
    else:
        print("✗ Redis连接失败")

    print(f"API文档: http://localhost:8000{SETTINGS.api_v1_str}/docs")


@APP.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的事件处理函数。"""
    print(f"Shutting down {SETTINGS.project_name}...")


# 健康检查端点
@APP.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": SETTINGS.project_name,
        "redis": redis_service.ping()
    }


# 根路径
@APP.get("/")
async def root():
    """根路径"""
    return {
        "message": f"Welcome to {SETTINGS.project_name}!",
        "docs": f"{SETTINGS.api_v1_str}/docs",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(APP, host="0.0.0.0", port=8000)
