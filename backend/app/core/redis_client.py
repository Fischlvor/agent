"""Redis客户端模块，提供Redis连接和操作。"""

from datetime import timedelta
from typing import Optional, Dict, Any
import json
import hashlib

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

    # ==================== 工具调用结果缓存 ====================

    def _generate_tool_cache_key(self, tool_name: str, tool_args: Dict[str, Any]) -> str:
        """生成工具调用缓存的键

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            缓存键
        """
        # 对参数进行排序并序列化，保证相同参数生成相同的hash
        args_str = json.dumps(tool_args, sort_keys=True, ensure_ascii=False)
        args_hash = hashlib.md5(args_str.encode()).hexdigest()
        return f"tool_cache:{tool_name}:{args_hash}"

    def get_tool_result(self, tool_name: str, tool_args: Dict[str, Any]) -> Optional[str]:
        """获取工具调用缓存结果

        Args:
            tool_name: 工具名称
            tool_args: 工具参数

        Returns:
            缓存的结果，如果不存在返回None
        """
        key = self._generate_tool_cache_key(tool_name, tool_args)
        return self.client.get(key)

    def save_tool_result(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        result: str,
        expire_seconds: int = 3600
    ) -> bool:
        """保存工具调用结果到缓存

        Args:
            tool_name: 工具名称
            tool_args: 工具参数
            result: 工具执行结果
            expire_seconds: 过期时间（秒），默认1小时

        Returns:
            是否保存成功
        """
        key = self._generate_tool_cache_key(tool_name, tool_args)
        return self.client.setex(key, expire_seconds, result)

    # ==================== 用户偏好/配置缓存 ====================

    def get_user_preference(self, user_id: str, key: str) -> Optional[str]:
        """获取用户偏好设置

        Args:
            user_id: 用户ID
            key: 配置键（如 'system_prompt', 'default_model' 等）

        Returns:
            配置值，如果不存在返回None
        """
        cache_key = f"user_pref:{user_id}:{key}"
        return self.client.get(cache_key)

    def save_user_preference(
        self,
        user_id: str,
        key: str,
        value: str,
        expire_seconds: int = 86400
    ) -> bool:
        """保存用户偏好设置

        Args:
            user_id: 用户ID
            key: 配置键
            value: 配置值
            expire_seconds: 过期时间（秒），默认24小时

        Returns:
            是否保存成功
        """
        cache_key = f"user_pref:{user_id}:{key}"
        return self.client.setex(cache_key, expire_seconds, value)

    def delete_user_preference(self, user_id: str, key: str) -> bool:
        """删除用户偏好设置

        Args:
            user_id: 用户ID
            key: 配置键

        Returns:
            是否删除成功
        """
        cache_key = f"user_pref:{user_id}:{key}"
        return self.client.delete(cache_key) > 0

    # ==================== 聊天历史摘要缓存 ====================

    def get_session_summary(self, session_id: str) -> Optional[str]:
        """获取会话历史摘要

        Args:
            session_id: 会话ID

        Returns:
            摘要内容，如果不存在返回None
        """
        key = f"session_summary:{session_id}"
        return self.client.get(key)

    def save_session_summary(
        self,
        session_id: str,
        summary: str,
        expire_seconds: int = 7200
    ) -> bool:
        """保存会话历史摘要

        Args:
            session_id: 会话ID
            summary: 摘要内容
            expire_seconds: 过期时间（秒），默认2小时

        Returns:
            是否保存成功
        """
        key = f"session_summary:{session_id}"
        return self.client.setex(key, expire_seconds, summary)

    def delete_session_summary(self, session_id: str) -> bool:
        """删除会话历史摘要（会话更新时）

        Args:
            session_id: 会话ID

        Returns:
            是否删除成功
        """
        key = f"session_summary:{session_id}"
        return self.client.delete(key) > 0

    # ==================== API 调用频率限制 ====================

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int]:
        """检查是否超过频率限制（基于固定窗口）

        使用 Lua 脚本保证原子性，避免竞态条件

        Args:
            key: 限流键（如 user:123 或 ip:127.0.0.1）
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口（秒）

        Returns:
            (是否允许请求, 剩余请求数)
        """
        rate_key = f"rate_limit:{key}"

        # Lua 脚本：原子性地执行 INCR 和 EXPIRE
        # 返回值：当前计数
        lua_script = """
        local current = redis.call('INCR', KEYS[1])
        if current == 1 then
            redis.call('EXPIRE', KEYS[1], ARGV[1])
        end
        return current
        """

        # 执行 Lua 脚本
        current_count = self.client.eval(lua_script, 1, rate_key, window_seconds)

        if current_count > max_requests:
            # 超过限制
            return (False, 0)

        return (True, max_requests - current_count)

    def reset_rate_limit(self, key: str) -> bool:
        """重置频率限制（管理员操作）

        Args:
            key: 限流键

        Returns:
            是否重置成功
        """
        rate_key = f"rate_limit:{key}"
        return self.client.delete(rate_key) > 0


# 创建全局Redis服务实例
redis_service = RedisService()

