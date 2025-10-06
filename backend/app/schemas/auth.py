"""认证相关的Schema定义。"""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator


# ==================== 注册相关 ====================

class RegisterRequest(BaseModel):
    """用户注册请求"""
    username: str = Field(..., min_length=3, max_length=50, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=6, max_length=100, description="密码")
    full_name: Optional[str] = Field(None, max_length=100, description="全名")

    @validator("username")
    def username_alphanumeric(cls, v):
        """验证用户名只包含字母、数字和下划线"""
        if not v.replace("_", "").isalnum():
            raise ValueError("用户名只能包含字母、数字和下划线")
        return v


class RegisterResponse(BaseModel):
    """用户注册响应"""
    message: str = "注册成功，请查收验证邮件"
    user_id: UUID
    email: str


# ==================== 登录相关 ====================

class PasswordLoginRequest(BaseModel):
    """密码登录请求"""
    login: str = Field(..., description="用户名或邮箱")
    password: str = Field(..., description="密码")


class SendLoginCodeRequest(BaseModel):
    """发送登录验证码请求"""
    email: EmailStr = Field(..., description="邮箱")


class EmailCodeLoginRequest(BaseModel):
    """邮箱验证码登录请求"""
    email: EmailStr = Field(..., description="邮箱")
    code: str = Field(..., min_length=6, max_length=6, description="6位验证码")


class LoginResponse(BaseModel):
    """登录响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # 秒
    user: dict


class SendLoginCodeResponse(BaseModel):
    """发送登录验证码响应"""
    message: str = "验证码已发送到您的邮箱"
    expires_in: int = 300  # 5分钟


# ==================== Token相关 ====================

class RefreshTokenRequest(BaseModel):
    """刷新Token请求（可选，也可以从Cookie读取）"""
    refresh_token: Optional[str] = None


class RefreshTokenResponse(BaseModel):
    """刷新Token响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    """登出请求（可选）"""
    refresh_token: Optional[str] = None


class LogoutResponse(BaseModel):
    """登出响应"""
    message: str = "登出成功"


# ==================== 邮箱验证相关 ====================

class VerifyEmailRequest(BaseModel):
    """验证邮箱请求"""
    token: str = Field(..., description="验证token")


class VerifyEmailResponse(BaseModel):
    """验证邮箱响应"""
    message: str = "邮箱验证成功"
    user_id: UUID


class ResendVerificationRequest(BaseModel):
    """重新发送验证邮件请求"""
    email: EmailStr = Field(..., description="邮箱")


class ResendVerificationResponse(BaseModel):
    """重新发送验证邮件响应"""
    message: str = "验证邮件已重新发送"


# ==================== 密码重置相关 ====================

class ForgotPasswordRequest(BaseModel):
    """忘记密码请求"""
    email: EmailStr = Field(..., description="邮箱")


class ForgotPasswordResponse(BaseModel):
    """忘记密码响应"""
    message: str = "密码重置邮件已发送"


class ResetPasswordRequest(BaseModel):
    """重置密码请求"""
    token: str = Field(..., description="重置token")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class ResetPasswordResponse(BaseModel):
    """重置密码响应"""
    message: str = "密码重置成功"


# ==================== Token Payload ====================

class TokenPayload(BaseModel):
    """Token载荷"""
    sub: Optional[str] = None  # subject (user_id)
    exp: Optional[int] = None  # expiration time
    type: Optional[str] = None  # token type
    jti: Optional[str] = None  # JWT ID

