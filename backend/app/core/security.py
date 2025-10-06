"""安全相关工具模块，包括JWT、密码加密、验证码生成等。"""

import random
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import SETTINGS

# 密码加密上下文（使用bcrypt）
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """加密密码（自动加盐）

    Args:
        password: 明文密码

    Returns:
        加密后的密码哈希

    Note:
        bcrypt限制密码最长72字节，超过部分会自动截断
    """
    # bcrypt限制密码最长72字节，确保不会超过
    if len(password.encode('utf-8')) > 72:
        # 截断到72字节
        password_bytes = password.encode('utf-8')[:72]
        password = password_bytes.decode('utf-8', errors='ignore')
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码

    Args:
        plain_password: 明文密码
        hashed_password: 加密后的密码哈希

    Returns:
        密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any]) -> str:
    """创建Access Token (JWT)

    Args:
        data: 要编码的数据（通常包含user_id等）

    Returns:
        JWT token字符串
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=SETTINGS.access_token_expire_minutes)
    to_encode.update({
        "exp": expire,
        "type": "access",
        "jti": str(uuid4())  # JWT ID，用于黑名单
    })
    encoded_jwt = jwt.encode(
        to_encode,
        SETTINGS.access_token_secret,
        algorithm=SETTINGS.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token() -> str:
    """创建Refresh Token (UUID格式)

    Returns:
        UUID格式的refresh token
    """
    return str(uuid4())


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """解码Access Token

    Args:
        token: JWT token字符串

    Returns:
        解码后的payload，如果无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            SETTINGS.access_token_secret,
            algorithms=[SETTINGS.jwt_algorithm]
        )
        # 验证token类型
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_verification_token() -> str:
    """生成邮箱验证/密码重置token（安全随机字符串）

    Returns:
        32字节的URL安全随机字符串
    """
    return secrets.token_urlsafe(32)


def generate_login_code() -> str:
    """生成6位登录验证码

    Returns:
        6位数字验证码字符串
    """
    return str(random.randint(100000, 999999))


def create_email_verification_token(user_id: str) -> str:
    """创建邮箱验证token（JWT格式，24小时有效）

    Args:
        user_id: 用户ID

    Returns:
        JWT token字符串
    """
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "user_id": user_id,
        "exp": expire,
        "type": "email_verification"
    }
    return jwt.encode(
        to_encode,
        SETTINGS.access_token_secret,
        algorithm=SETTINGS.jwt_algorithm
    )


def decode_email_verification_token(token: str) -> Optional[str]:
    """解码邮箱验证token

    Args:
        token: JWT token字符串

    Returns:
        用户ID，如果无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            SETTINGS.access_token_secret,
            algorithms=[SETTINGS.jwt_algorithm]
        )
        if payload.get("type") != "email_verification":
            return None
        return payload.get("user_id")
    except JWTError:
        return None


def create_password_reset_token(user_id: str) -> str:
    """创建密码重置token（JWT格式，1小时有效）

    Args:
        user_id: 用户ID

    Returns:
        JWT token字符串
    """
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {
        "user_id": user_id,
        "exp": expire,
        "type": "password_reset"
    }
    return jwt.encode(
        to_encode,
        SETTINGS.access_token_secret,
        algorithm=SETTINGS.jwt_algorithm
    )


def decode_password_reset_token(token: str) -> Optional[str]:
    """解码密码重置token

    Args:
        token: JWT token字符串

    Returns:
        用户ID，如果无效则返回None
    """
    try:
        payload = jwt.decode(
            token,
            SETTINGS.access_token_secret,
            algorithms=[SETTINGS.jwt_algorithm]
        )
        if payload.get("type") != "password_reset":
            return None
        return payload.get("user_id")
    except JWTError:
        return None

