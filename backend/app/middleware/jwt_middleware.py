"""JWT认证中间件，自动解析token并设置用户信息到request.state"""

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.security import decode_access_token

logger = logging.getLogger(__name__)


class JWTMiddleware(BaseHTTPMiddleware):
    """JWT认证中间件

    从 Authorization header 解析 JWT token，并将用户信息设置到 request.state.user_id
    这样后续的中间件（如限流）可以直接使用用户ID
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # 尝试从 Authorization header 获取 token
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)

                if payload and "sub" in payload:
                    # 设置用户ID到request.state，供后续中间件和端点使用
                    request.state.user_id = payload["sub"]
                    #logger.info(f"JWT认证成功: user_id={payload['sub']}")
            except Exception as e:
                # Token 无效或过期，不设置用户信息，继续处理请求
                logger.info(f"JWT解析失败: {e}")
                pass

        # 继续处理请求
        response = await call_next(request)
        return response

