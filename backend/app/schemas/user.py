"""用户相关的Schema定义。"""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    """用户基础Schema"""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """创建用户的请求Schema"""
    password: str


class UserUpdate(BaseModel):
    """更新用户信息请求"""
    full_name: Optional[str] = Field(None, max_length=100, description="全名")
    avatar_url: Optional[str] = Field(None, max_length=255, description="头像URL")
    bio: Optional[str] = Field(None, description="个人简介")


class UserResponse(BaseModel):
    """用户的响应Schema"""
    id: int
    username: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    role: str
    is_active: bool
    is_verified: bool
    last_login_at: Optional[datetime] = None
    login_count: int
    preferences: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        """Pydantic配置"""
        from_attributes = True


class ChangePasswordRequest(BaseModel):
    """修改密码请求"""
    old_password: str = Field(..., description="旧密码")
    new_password: str = Field(..., min_length=6, max_length=100, description="新密码")


class ChangePasswordResponse(BaseModel):
    """修改密码响应"""
    message: str = "密码修改成功"


class UserPreferencesUpdate(BaseModel):
    """更新用户偏好设置请求"""
    preferences: Dict[str, Any] = Field(..., description="偏好设置JSON对象")


class UserPreferencesResponse(BaseModel):
    """用户偏好设置响应"""
    preferences: Dict[str, Any]


class DeleteAccountRequest(BaseModel):
    """注销账户请求"""
    password: str = Field(..., description="密码确认")
    confirmation: str = Field(..., description="确认文本，必须是'DELETE'")


class DeleteAccountResponse(BaseModel):
    """注销账户响应"""
    message: str = "账户已注销"


# ==================== 管理员相关 ====================

class UserListQuery(BaseModel):
    """用户列表查询参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")
    search: Optional[str] = Field(None, description="搜索关键词（用户名/邮箱）")
    role: Optional[str] = Field(None, description="角色筛选")
    is_active: Optional[bool] = Field(None, description="是否激活")
    is_verified: Optional[bool] = Field(None, description="是否已验证")


class UserListResponse(BaseModel):
    """用户列表响应"""
    total: int
    page: int
    page_size: int
    users: list[UserResponse]


class AdminUserUpdate(BaseModel):
    """管理员更新用户信息"""
    full_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern="^(user|admin)$", description="用户角色")
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class UpdateUserStatusRequest(BaseModel):
    """更新用户状态请求"""
    is_active: bool = Field(..., description="是否激活")
