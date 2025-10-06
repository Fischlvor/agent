"""Redis客户端模块，提供Redis连接和操作。"""

from datetime import timedelta
from typing import Optional

import redis

from app.core.config import SETTINGS

# 创建Redis连接池（添加超时和重连配置）
_redis_pool = redis.ConnectionPool(
    host=SETTINGS.redis_host,
    port=SETTINGS.redis_port,
    password=SETTINGS.redis_password,
    db=SETTINGS.redis_db,
    decode_responses=SETTINGS.redis_decode_responses,
    max_connections=50,
    socket_connect_timeout=5,  # 连接超时5秒
    socket_timeout=5,  # 读写超时5秒
    socket_keepalive=True,  # 启用TCP keepalive
    socket_keepalive_options=None,
    retry_on_timeout=True,  # 超时自动重试
    health_check_interval=30  # 每30秒检查连接健康状态
)

# 创建Redis客户端
redis_client = redis.Redis(
    connection_pool=_redis_pool,
    retry_on_error=[redis.exceptions.ConnectionError, redis.exceptions.TimeoutError]  # 遇到连接错误自动重试
)


class RedisService:
    """Redis服务类，提供常用的Redis操作"""

    def __init__(self):
        self.client = redis_client

    # ==================== 登录验证码相关 ====================

    def save_login_code(self, email: str, code: str, expire_seconds: int = 300) -> bool:
        """保存登录验证码（5分钟有效）

        Args:
            email: 用户邮箱
            code: 验证码
            expire_seconds: 过期时间（秒），默认300秒（5分钟）

        Returns:
            是否保存成功
        """
        key = f"login_code:{email}"
        return self.client.setex(key, expire_seconds, code)

    def get_login_code(self, email: str) -> Optional[str]:
        """获取登录验证码

        Args:
            email: 用户邮箱

        Returns:
            验证码，如果不存在或已过期返回None
        """
        key = f"login_code:{email}"
        return self.client.get(key)

    def delete_login_code(self, email: str) -> bool:
        """删除登录验证码（使用后删除）

        Args:
            email: 用户邮箱

        Returns:
            是否删除成功
        """
        key = f"login_code:{email}"
        return self.client.delete(key) > 0

    # ==================== Refresh Token相关 ====================

    def save_refresh_token(
        self,
        token: str,
        user_id: str,
        expire_days: int = 7
    ) -> bool:
        """保存Refresh Token

        Args:
            token: refresh token（UUID格式）
            user_id: 用户ID
            expire_days: 过期天数，默认7天

        Returns:
            是否保存成功
        """
        key = f"refresh_token:{token}"
        expire_seconds = expire_days * 24 * 60 * 60
        return self.client.setex(key, expire_seconds, user_id)

    def get_refresh_token(self, token: str) -> Optional[str]:
        """获取Refresh Token对应的用户ID

        Args:
            token: refresh token

        Returns:
            用户ID，如果不存在或已过期返回None
        """
        key = f"refresh_token:{token}"
        return self.client.get(key)

    def delete_refresh_token(self, token: str) -> bool:
        """删除Refresh Token（用户登出时）

        Args:
            token: refresh token

        Returns:
            是否删除成功
        """
        key = f"refresh_token:{token}"
        return self.client.delete(key) > 0

    def delete_user_refresh_tokens(self, user_id: str) -> int:
        """删除用户的所有Refresh Token（修改密码/强制登出时）

        Args:
            user_id: 用户ID

        Returns:
            删除的token数量
        """
        # 查找该用户的所有refresh token
        pattern = "refresh_token:*"
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = self.client.scan(cursor, match=pattern, count=100)
            for key in keys:
                value = self.client.get(key)
                if value == user_id:
                    self.client.delete(key)
                    deleted_count += 1

            if cursor == 0:
                break

        return deleted_count

    # ==================== Access Token黑名单（可选）====================

    def add_token_to_blacklist(self, jti: str, expire_minutes: int = 60) -> bool:
        """将Access Token加入黑名单（强制登出时使用）

        Args:
            jti: JWT ID（从token中提取）
            expire_minutes: 过期时间（分钟），应与access token有效期一致

        Returns:
            是否添加成功
        """
        key = f"token_blacklist:{jti}"
        expire_seconds = expire_minutes * 60
        return self.client.setex(key, expire_seconds, "1")

    def is_token_blacklisted(self, jti: str) -> bool:
        """检查Access Token是否在黑名单中

        Args:
            jti: JWT ID

        Returns:
            是否在黑名单中
        """
        key = f"token_blacklist:{jti}"
        return self.client.exists(key) > 0

    # ==================== 通用操作 ====================

    def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """设置键值对

        Args:
            key: 键
            value: 值
            expire: 过期时间（秒），None表示不过期

        Returns:
            是否设置成功
        """
        if expire:
            return self.client.setex(key, expire, value)
        return self.client.set(key, value)

    def get(self, key: str) -> Optional[str]:
        """获取值

        Args:
            key: 键

        Returns:
            值，如果不存在返回None
        """
        return self.client.get(key)

    def delete(self, key: str) -> bool:
        """删除键

        Args:
            key: 键

        Returns:
            是否删除成功
        """
        return self.client.delete(key) > 0

    def exists(self, key: str) -> bool:
        """检查键是否存在

        Args:
            key: 键

        Returns:
            是否存在
        """
        return self.client.exists(key) > 0

    def ping(self) -> bool:
        """测试Redis连接

        Returns:
            连接是否正常
        """
        try:
            return self.client.ping()
        except Exception:
            return False


# 创建全局Redis服务实例
redis_service = RedisService()

