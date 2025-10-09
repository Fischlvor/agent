"""用户模型定义"""

from typing import Any, Dict

from sqlalchemy import Boolean, Column, DateTime, Integer, JSON, String, Text

from app.models.base import BaseModel


class User(BaseModel):
    """用户模型"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="用户主键ID")
    username = Column(String(50), unique=True, nullable=False, comment="用户名，用于登录")
    email = Column(String(100), unique=True, nullable=False, comment="用户邮箱，用于登录和通知")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    full_name = Column(String(100), nullable=True, comment="用户全名")
    avatar_url = Column(String(255), nullable=True, comment="用户头像URL")
    bio = Column(Text, nullable=True, comment="用户简介")
    role = Column(String(20), default="user", comment="用户角色，如user、admin等")
    is_active = Column(Boolean, default=True, comment="用户是否激活")
    is_verified = Column(Boolean, default=False, comment="用户是否已验证邮箱")
    verification_token = Column(String(255), nullable=True, comment="邮箱验证令牌")
    reset_password_token = Column(String(255), nullable=True, comment="密码重置令牌")
    reset_password_expires = Column(DateTime, nullable=True, comment="密码重置令牌过期时间")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")
    login_count = Column(Integer, default=0, comment="登录次数")
    preferences = Column(JSON, default={}, comment="用户偏好设置，JSON格式")

    def __repr__(self) -> str:
        """返回用户的字符串表示"""
        return f"<User {self.username}>"

    @property
    def is_admin(self) -> bool:
        """判断用户是否为管理员"""
        return self.role == "admin"

    # 重写父类方法，添加新参数
    # pylint: disable=arguments-differ
    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """将用户转换为字典，可选是否包含敏感信息

        Args:
            include_sensitive: 是否包含敏感信息

        Returns:
            用户信息字典
        """
        user_dict = super().to_dict()

        # 移除敏感信息
        if not include_sensitive:
            sensitive_fields = [
                "password_hash",
                "verification_token",
                "reset_password_token",
                "reset_password_expires",
            ]
            for field in sensitive_fields:
                if field in user_dict:
                    user_dict.pop(field)

        return user_dict
