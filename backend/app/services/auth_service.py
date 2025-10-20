"""认证服务模块，处理认证相关业务逻辑。"""

from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.core.config import SETTINGS
from app.core.email import email_service
from app.core.redis_client import redis_service
from app.core.security import (
    create_access_token,
    create_email_verification_token,
    create_password_reset_token,
    create_refresh_token,
    decode_email_verification_token,
    decode_password_reset_token,
    generate_login_code,
    hash_password,
    verify_password,
)
from app.models.user import User
from app.services.user_service import UserService


class AuthService:
    """认证服务类"""

    def __init__(self, db: Session):
        self.db = db
        self.user_service = UserService(db)

    # ==================== 注册相关 ====================

    def register_user(
        self,
        username: str,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Tuple[User, bool]:
        """注册新用户

        Args:
            username: 用户名
            email: 邮箱
            password: 密码
            full_name: 全名

        Returns:
            (用户对象, 是否发送邮件成功)

        Raises:
            ValueError: 用户名或邮箱已存在
        """
        # 检查用户名是否已存在
        existing_user = self.db.query(User).filter(User.username == username).first()
        if existing_user:
            raise ValueError("用户名已存在")

        # 检查邮箱是否已存在
        existing_email = self.db.query(User).filter(User.email == email).first()
        if existing_email:
            raise ValueError("邮箱已被注册")

        # 创建用户
        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            is_verified=False,
            role="user"
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        # 发送验证邮件
        email_sent = self._send_verification_email(user)

        return user, email_sent

    def _send_verification_email(self, user: User) -> bool:
        """发送验证邮件（内部方法）"""
        try:
            # 生成验证token
            token = create_email_verification_token(str(user.id))

            # 构建验证链接
            verification_link = (
                f"{SETTINGS.frontend_base_url}"
                f"{SETTINGS.frontend_verify_email_path}?token={token}"
            )

            # 发送邮件
            return email_service.send_verification_email(
                to_email=user.email,
                username=user.username,
                verification_link=verification_link
            )
        except Exception as e:
            print(f"❌ 发送验证邮件失败: {e}")
            return False

    def verify_email(self, token: str) -> User:
        """验证邮箱

        Args:
            token: 验证token

        Returns:
            用户对象

        Raises:
            ValueError: token无效或已过期
        """
        # 解码token
        user_id = decode_email_verification_token(token)
        if not user_id:
            raise ValueError("验证链接无效或已过期")

        # 查找用户
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise ValueError("用户不存在")

        # 更新验证状态
        if user.is_verified:
            raise ValueError("邮箱已验证，无需重复验证")

        user.is_verified = True
        self.db.commit()
        self.db.refresh(user)

        return user

    def resend_verification_email(self, email: str) -> bool:
        """重新发送验证邮件

        Args:
            email: 邮箱

        Returns:
            是否发送成功

        Raises:
            ValueError: 邮箱不存在或已验证
        """
        # 查找用户
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("邮箱未注册")

        if user.is_verified:
            raise ValueError("邮箱已验证，无需重复发送")

        # 发送邮件
        return self._send_verification_email(user)

    # ==================== 登录相关 ====================

    def password_login(self, login: str, password: str) -> Tuple[User, str, str]:
        """密码登录

        Args:
            login: 用户名或邮箱
            password: 密码

        Returns:
            (用户对象, access_token, refresh_token)

        Raises:
            ValueError: 用户不存在、密码错误、账户未激活等
        """
        # 查找用户（支持用户名或邮箱登录）
        user = self.db.query(User).filter(
            (User.username == login) | (User.email == login)
        ).first()

        if not user:
            raise ValueError("用户名或邮箱不存在")

        # 验证密码
        if not verify_password(password, user.password_hash):
            raise ValueError("密码错误")

        # 检查账户状态
        if not user.is_active:
            raise ValueError("账户已被禁用")

        if not user.is_verified:
            raise ValueError("邮箱未验证，请先验证邮箱")

        # 生成tokens
        access_token, refresh_token = self._generate_tokens(user)

        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        self.db.commit()

        return user, access_token, refresh_token

    def send_login_code(self, email: str) -> bool:
        """发送登录验证码

        Args:
            email: 邮箱

        Returns:
            是否发送成功

        Raises:
            ValueError: 邮箱不存在或账户未激活
        """
        # 查找用户
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("邮箱未注册")

        if not user.is_active:
            raise ValueError("账户已被禁用")

        if not user.is_verified:
            raise ValueError("邮箱未验证，请先验证邮箱")

        # 生成验证码
        code = generate_login_code()

        # 保存到Redis（5分钟有效）
        redis_service.save_login_code(email, code, expire_seconds=300)

        # 发送邮件
        try:
            return email_service.send_login_code_email(
                to_email=email,
                username=user.username,
                code=code
            )
        except Exception as e:
            print(f"❌ 发送登录验证码失败: {e}")
            return False

    def email_code_login(self, email: str, code: str) -> Tuple[User, str, str]:
        """邮箱验证码登录

        Args:
            email: 邮箱
            code: 验证码

        Returns:
            (用户对象, access_token, refresh_token)

        Raises:
            ValueError: 验证码错误或已过期
        """
        # 查找用户
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("邮箱未注册")

        # 验证验证码
        stored_code = redis_service.get_login_code(email)
        if not stored_code:
            raise ValueError("验证码已过期，请重新获取")

        if stored_code != code:
            raise ValueError("验证码错误")

        # 删除已使用的验证码
        redis_service.delete_login_code(email)

        # 检查账户状态
        if not user.is_active:
            raise ValueError("账户已被禁用")

        # 生成tokens
        access_token, refresh_token = self._generate_tokens(user)

        # 更新登录信息
        user.last_login_at = datetime.utcnow()
        user.login_count += 1
        self.db.commit()

        return user, access_token, refresh_token

    def _generate_tokens(self, user: User) -> Tuple[str, str]:
        """生成access和refresh tokens（内部方法）"""
        # 先生成Refresh Token
        refresh_token = create_refresh_token()

        # 生成Access Token（绑定 refresh_token_id）
        access_token = create_access_token({
            "sub": str(user.id),
            "username": user.username,
            "role": user.role,
            "refresh_token_id": refresh_token  # ✅ 绑定 refresh token
        })

        # 保存Refresh Token到Redis（7天有效）
        redis_service.save_refresh_token(
            token=refresh_token,
            user_id=str(user.id),
            expire_days=SETTINGS.refresh_token_expire_days
        )

        return access_token, refresh_token

    # ==================== Token管理 ====================

    def refresh_access_token(self, refresh_token: str) -> Tuple[str, str, User]:
        """刷新Access Token

        Args:
            refresh_token: refresh token

        Returns:
            (新的access_token, 新的refresh_token, 用户对象)

        Raises:
            ValueError: refresh token无效或已过期
        """
        # 验证Refresh Token
        user_id = redis_service.get_refresh_token(refresh_token)
        if not user_id:
            raise ValueError("Refresh token无效或已过期")

        # 查找用户
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise ValueError("用户不存在")

        if not user.is_active:
            raise ValueError("账户已被禁用")

        # 删除旧的Refresh Token
        redis_service.delete_refresh_token(refresh_token)

        # 生成新的tokens
        new_access_token, new_refresh_token = self._generate_tokens(user)

        return new_access_token, new_refresh_token, user

    def logout(self, refresh_token: str) -> bool:
        """登出

        Args:
            refresh_token: refresh token

        Returns:
            是否成功
        """
        # 删除Refresh Token
        return redis_service.delete_refresh_token(refresh_token)

    # ==================== 密码重置相关 ====================

    def forgot_password(self, email: str) -> bool:
        """忘记密码

        Args:
            email: 邮箱

        Returns:
            是否发送成功

        Raises:
            ValueError: 邮箱不存在
        """
        # 查找用户
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("邮箱未注册")

        # 生成重置token
        token = create_password_reset_token(str(user.id))

        # 构建重置链接
        reset_link = (
            f"{SETTINGS.frontend_base_url}"
            f"{SETTINGS.frontend_reset_password_path}?token={token}"
        )

        # 发送邮件
        try:
            return email_service.send_password_reset_email(
                to_email=user.email,
                username=user.username,
                reset_link=reset_link
            )
        except Exception as e:
            print(f"❌ 发送密码重置邮件失败: {e}")
            return False

    def reset_password(self, token: str, new_password: str) -> User:
        """重置密码

        Args:
            token: 重置token
            new_password: 新密码

        Returns:
            用户对象

        Raises:
            ValueError: token无效或已过期
        """
        # 解码token
        user_id = decode_password_reset_token(token)
        if not user_id:
            raise ValueError("重置链接无效或已过期")

        # 查找用户
        user = self.db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise ValueError("用户不存在")

        # 更新密码
        user.password_hash = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)

        # 删除该用户的所有Refresh Token（强制重新登录）
        redis_service.delete_user_refresh_tokens(str(user.id))

        return user

    # ==================== 用户查询 ====================

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """根据ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            用户对象，不存在返回None
        """
        return self.db.query(User).filter(User.id == user_id).first()

