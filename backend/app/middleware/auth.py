"""认证中间件，提供JWT验证和权限检查。"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.redis_client import redis_service
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.user import User

# HTTP Bearer认证方案
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """获取当前登录用户（JWT验证）

    Args:
        credentials: HTTP认证凭证
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    token = credentials.credentials

    # 解码token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 获取用户ID
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token载荷",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查token是否在黑名单中（可选）
    jti = payload.get("jti")
    if jti and redis_service.is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 查询用户
    try:
        user_id = int(user_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="邮箱未验证，请先验证邮箱",
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """获取当前活跃用户（已验证邮箱）

    Args:
        current_user: 当前用户

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果用户未激活或未验证
    """
    # 在get_current_user中已经检查过了，这里直接返回
    return current_user


def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """要求管理员权限

    Args:
        current_user: 当前用户

    Returns:
        当前用户对象（管理员）

    Raises:
        HTTPException: 如果用户不是管理员
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """获取当前用户（可选，不强制要求认证）

    Args:
        credentials: HTTP认证凭证（可选）
        db: 数据库会话

    Returns:
        当前用户对象，如果未认证返回None
    """
    if not credentials:
        return None

    try:
        return get_current_user(credentials, db)
    except HTTPException:
        return None


async def get_current_user_ws(token: str, db: Session) -> User:
    """WebSocket专用：获取当前登录用户（JWT验证）

    Args:
        token: JWT token字符串
        db: 数据库会话

    Returns:
        当前用户对象

    Raises:
        HTTPException: 如果token无效或用户不存在
    """
    # 解码token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证"
        )

    # 获取用户ID
    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的token载荷"
        )

    # 检查token是否在黑名单中
    jti = payload.get("jti")
    if jti and redis_service.is_token_blacklisted(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token已失效"
        )

    # 查询用户
    try:
        user_id = int(user_id_str)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的用户ID"
        ) from exc

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在"
        )

    # 检查用户状态
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="邮箱未验证，请先验证邮箱"
        )

    return user

