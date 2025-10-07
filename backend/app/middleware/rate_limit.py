"""API 频率限制中间件"""

import logging
from typing import Callable

from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis_client import redis_service

LOGGER = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 频率限制中间件

    基于用户ID或IP的请求频率限制
    """

    def __init__(
        self,
        app,
        max_requests: int = 60,
        window_seconds: int = 60,
        exclude_paths: list[str] = None
    ):
        """初始化频率限制中间件

        Args:
            app: FastAPI 应用
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）
            exclude_paths: 不需要限流的路径列表
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.exclude_paths = exclude_paths or [
            "/api/v1/auth/login",
            "/api/v1/auth/send-code",
            "/api/v1/health",
            "/docs",
            "/openapi.json"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # 检查是否需要限流
        if self._should_skip(request):
            return await call_next(request)

        # 获取限流键（优先使用用户ID，否则使用IP）
        rate_limit_key = self._get_rate_limit_key(request)

        # 检查频率限制
        allowed, remaining = redis_service.check_rate_limit(
            key=rate_limit_key,
            max_requests=self.max_requests,
            window_seconds=self.window_seconds
        )

        if not allowed:
            LOGGER.warning(f"频率限制触发: {rate_limit_key}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="请求过于频繁，请稍后再试",
                headers={
                    "Retry-After": str(self.window_seconds),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(self.window_seconds)
                }
            )

        # 继续处理请求，并在响应头中添加频率限制信息
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(self.window_seconds)

        return response

    def _should_skip(self, request: Request) -> bool:
        """判断是否跳过频率限制

        Args:
            request: 请求对象

        Returns:
            是否跳过
        """
        # 检查路径是否在排除列表中
        path = request.url.path
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True

        # WebSocket 连接不限流
        if request.url.path.endswith("/ws"):
            return True

        return False

    def _get_rate_limit_key(self, request: Request) -> str:
        """获取频率限制键

        Args:
            request: 请求对象

        Returns:
            限流键
        """
        # 优先使用用户ID（从请求状态中获取）
        if hasattr(request.state, "user") and request.state.user:
            user_id = getattr(request.state.user, "id", None)
            if user_id:
                return f"rate_limit:user:{user_id}"

        # 否则使用客户端IP
        client_ip = request.client.host if request.client else "unknown"
        return f"rate_limit:ip:{client_ip}"

