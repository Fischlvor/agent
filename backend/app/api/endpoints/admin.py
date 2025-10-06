"""管理员功能API端点"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import require_admin
from app.models.user import User
from app.schemas.user import (
    AdminUserUpdate,
    UpdateUserStatusRequest,
    UserListResponse,
    UserResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/users", response_model=UserListResponse)
def get_users_list(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: str = Query(None, description="搜索关键词（用户名/邮箱/全名）"),
    role: str = Query(None, description="角色筛选"),
    is_active: bool = Query(None, description="激活状态筛选"),
    is_verified: bool = Query(None, description="验证状态筛选"),
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取用户列表（管理员）

    - 需要管理员权限
    - 支持分页、搜索、筛选
    """
    user_service = UserService(db)

    users, total = user_service.get_users_list(
        page=page,
        page_size=page_size,
        search=search,
        role=role,
        is_active=is_active,
        is_verified=is_verified
    )

    return UserListResponse(
        total=total,
        page=page,
        page_size=page_size,
        users=users
    )


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user_detail(
    user_id: UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """获取指定用户详情（管理员）

    - 需要管理员权限
    """
    user_service = UserService(db)

    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    request: AdminUserUpdate,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """更新用户信息（管理员）

    - 需要管理员权限
    - 可以更新角色、激活状态、验证状态等
    """
    user_service = UserService(db)

    # 检查用户是否存在
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    # 构建更新数据
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.role is not None:
        update_data["role"] = request.role
    if request.is_active is not None:
        update_data["is_active"] = request.is_active
    if request.is_verified is not None:
        update_data["is_verified"] = request.is_verified

    updated_user = user_service.admin_update_user(user_id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )

    return updated_user


@router.delete("/users/{user_id}")
def delete_user(
    user_id: UUID,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """删除用户（管理员）

    - 需要管理员权限
    - 硬删除，不可恢复
    - 不能删除自己
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能删除自己"
        )

    user_service = UserService(db)

    success = user_service.admin_delete_user(user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return {"message": "用户已删除"}


@router.put("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: UUID,
    request: UpdateUserStatusRequest,
    current_admin: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """启用/禁用用户（管理员）

    - 需要管理员权限
    - 禁用用户会清除其所有登录状态
    - 不能禁用自己
    """
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="不能禁用自己"
        )

    user_service = UserService(db)

    updated_user = user_service.update_user_status(user_id, request.is_active)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    return updated_user

