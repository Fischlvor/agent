"""用户服务模块，提供用户管理相关的业务逻辑。"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.redis_client import redis_service
from app.core.security import hash_password, verify_password
from app.models.user import User


class UserService:
    """用户服务类"""

    def __init__(self, db: Session):
        self.db = db

    # ==================== 用户查询 ====================

    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根据ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            用户对象，如果不存在返回None
        """
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户

        Args:
            username: 用户名

        Returns:
            用户对象，如果不存在返回None
        """
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """根据邮箱获取用户

        Args:
            email: 邮箱

        Returns:
            用户对象，如果不存在返回None
        """
        return self.db.query(User).filter(User.email == email).first()

    # ==================== 用户更新 ====================

    def update_user(
        self,
        user_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户信息

        Args:
            user_id: 用户ID
            update_data: 更新数据字典

        Returns:
            更新后的用户对象，如果用户不存在返回None
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # 更新字段
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """修改密码

        Args:
            user_id: 用户ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            (是否成功, 错误信息)
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在"

        # 验证旧密码
        if not verify_password(old_password, user.password_hash):
            return False, "旧密码错误"

        # 更新密码
        user.password_hash = hash_password(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()

        # 删除该用户的所有refresh token（强制重新登录）
        redis_service.delete_user_refresh_tokens(str(user.id))

        return True, None

    def update_preferences(
        self,
        user_id: UUID,
        preferences: Dict[str, Any]
    ) -> Optional[User]:
        """更新用户偏好设置

        Args:
            user_id: 用户ID
            preferences: 偏好设置字典

        Returns:
            更新后的用户对象，如果用户不存在返回None
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        user.preferences = preferences
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete_user(
        self,
        user_id: UUID,
        password: str,
        confirmation: str
    ) -> Tuple[bool, Optional[str]]:
        """删除用户账户（软删除，设置is_active=False）

        Args:
            user_id: 用户ID
            password: 密码确认
            confirmation: 确认文本（必须是"DELETE"）

        Returns:
            (是否成功, 错误信息)
        """
        if confirmation != "DELETE":
            return False, "确认文本不正确"

        user = self.get_user_by_id(user_id)
        if not user:
            return False, "用户不存在"

        # 验证密码
        if not verify_password(password, user.password_hash):
            return False, "密码错误"

        # 软删除：设置为不活跃
        user.is_active = False
        user.updated_at = datetime.utcnow()
        self.db.commit()

        # 删除该用户的所有refresh token
        redis_service.delete_user_refresh_tokens(str(user.id))

        return True, None

    # ==================== 管理员功能 ====================

    def get_users_list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_verified: Optional[bool] = None
    ) -> Tuple[List[User], int]:
        """获取用户列表（带分页和筛选）

        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            search: 搜索关键词（用户名/邮箱）
            role: 角色筛选
            is_active: 是否激活筛选
            is_verified: 是否已验证筛选

        Returns:
            (用户列表, 总数)
        """
        query = self.db.query(User)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    User.username.ilike(f"%{search}%"),
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )

        # 角色过滤
        if role:
            query = query.filter(User.role == role)

        # 激活状态过滤
        if is_active is not None:
            query = query.filter(User.is_active == is_active)

        # 验证状态过滤
        if is_verified is not None:
            query = query.filter(User.is_verified == is_verified)

        # 总数
        total = query.count()

        # 分页
        offset = (page - 1) * page_size
        users = query.order_by(User.created_at.desc()).offset(offset).limit(page_size).all()

        return users, total

    def admin_update_user(
        self,
        user_id: UUID,
        update_data: Dict[str, Any]
    ) -> Optional[User]:
        """管理员更新用户信息

        Args:
            user_id: 用户ID
            update_data: 更新数据（可以包含role, is_active, is_verified等）

        Returns:
            更新后的用户对象，如果用户不存在返回None
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        # 更新字段
        for key, value in update_data.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)

        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user

    def admin_delete_user(self, user_id: UUID) -> bool:
        """管理员删除用户（硬删除）

        Args:
            user_id: 用户ID

        Returns:
            是否删除成功
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False

        # 删除该用户的所有refresh token
        redis_service.delete_user_refresh_tokens(str(user.id))

        # 硬删除
        self.db.delete(user)
        self.db.commit()
        return True

    def update_user_status(
        self,
        user_id: UUID,
        is_active: bool
    ) -> Optional[User]:
        """更新用户激活状态

        Args:
            user_id: 用户ID
            is_active: 是否激活

        Returns:
            更新后的用户对象，如果用户不存在返回None
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None

        user.is_active = is_active
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)

        # 如果禁用用户，删除其所有refresh token
        if not is_active:
            redis_service.delete_user_refresh_tokens(str(user.id))

        return user

