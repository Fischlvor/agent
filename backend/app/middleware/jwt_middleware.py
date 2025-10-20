"""JWT认证中间件，自动解析token并设置用户信息到request.state"""

import logging
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, JSONResponse

from app.core.security import decode_access_token
from app.core.redis_client import redis_service

logger = logging.getLogger(__name__)


class JWTMiddleware(BaseHTTPMiddleware):
    """JWT认证中间件

    从 Authorization header 解析 JWT token，并将用户信息设置到 request.state.user_id
    这样后续的中间件（如限流）可以直接使用用户ID
    """

    # 不需要验证 token 的公开路径（使用 set 提高查找效率 O(1)）
    PUBLIC_PATHS = {
        "/api/v1/sso/auth/login/password",
        "/api/v1/sso/auth/login/email-code",
        "/api/v1/sso/auth/register",
        "/api/v1/sso/auth/refresh",  # ✅ refresh 接口应该跳过 JWT 验证
        "/api/v1/sso/auth/verify-email",
        "/api/v1/sso/auth/send-login-code",
        "/api/v1/sso/auth/resend-verification",
        "/api/v1/sso/auth/forgot-password",
        "/api/v1/sso/auth/reset-password",
        "/api/v1/docs",
        "/api/v1/openapi.json",
        "/api/v1/health",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """处理请求

        Args:
            request: 请求对象
            call_next: 下一个中间件或路由处理器

        Returns:
            响应对象
        """
        # ✅ O(1) 查找公开路径，跳过 JWT 验证
        if request.url.path in self.PUBLIC_PATHS:
            return await call_next(request)

        # 尝试从 Authorization header 获取 token
        auth_header = request.headers.get("Authorization")

        if auth_header and auth_header.startswith("Bearer "):
            try:
                token = auth_header.split(" ")[1]
                payload = decode_access_token(token)

                if payload and "sub" in payload:
                    # ✅ 验证绑定的 refresh token 是否还有效
                    refresh_token_id = payload.get("refresh_token_id")
                    if refresh_token_id:
                        # 检查 refresh token 是否还在 Redis 中
                        if redis_service.get_refresh_token(refresh_token_id):
                            # Refresh token 有效，允许访问
                            request.state.user_id = payload["sub"]
                            #logger.info("JWT认证成功: user_id=%s", payload['sub'])
                        else:
                            # ✅ Refresh token 已被删除（登出/过期），直接返回 401
                            logger.info("Access token 被拒绝: 绑定的 refresh token 已失效 (user_id=%s)", payload['sub'])
                            return JSONResponse(
                                status_code=401,
                                content={"detail": "Token已失效（会话已结束）"},
                                headers={"WWW-Authenticate": "Bearer"}
                            )
                    else:
                        # ✅ 没有 refresh_token_id，直接返回 401（不兼容旧版本）
                        logger.info("Access token 被拒绝: 缺少 refresh_token_id 绑定 (user_id=%s)", payload['sub'])
                        return JSONResponse(
                            status_code=401,
                            content={"detail": "Token格式不支持（请重新登录）"},
                            headers={"WWW-Authenticate": "Bearer"}
                        )
                else:
                    # ✅ Token 解析失败或载荷无效，直接返回 401
                    logger.warning("Token载荷无效")
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "无效的认证凭证"},
                        headers={"WWW-Authenticate": "Bearer"}
                    )
            except (IndexError, KeyError, ValueError) as e:
                # ✅ Token 格式错误，直接返回 401
                logger.warning("Token格式错误: %s", str(e))
                return JSONResponse(
                    status_code=401,
                    content={"detail": "无效的Token格式"},
                    headers={"WWW-Authenticate": "Bearer"}
                )
            except Exception as e:  # pylint: disable=broad-except
                # ✅ 系统错误（如 Redis 连接失败），返回 503
                logger.error("JWT中间件异常: %s", str(e), exc_info=True)
                return JSONResponse(
                    status_code=503,
                    content={"detail": "认证服务暂时不可用"},
                    headers={"WWW-Authenticate": "Bearer"}
                )

        # 继续处理请求
        response = await call_next(request)
        return response

