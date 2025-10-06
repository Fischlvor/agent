"""用户资源管理API端点"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    ChangePasswordResponse,
    DeleteAccountRequest,
    DeleteAccountResponse,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["用户管理"])


@router.get("/me", response_model=UserResponse)
def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户信息

    - 需要JWT认证
    - 返回当前登录用户的详细信息
    """
    return current_user


@router.put("/me", response_model=UserResponse)
def update_current_user(
    request: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新当前用户信息

    - 可以更新：全名、头像、简介
    - 不能更新：用户名、邮箱、角色
    """
    user_service = UserService(db)

    # 构建更新数据
    update_data = {}
    if request.full_name is not None:
        update_data["full_name"] = request.full_name
    if request.avatar_url is not None:
        update_data["avatar_url"] = request.avatar_url
    if request.bio is not None:
        update_data["bio"] = request.bio

    updated_user = user_service.update_user(current_user.id, update_data)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )

    return updated_user


@router.delete("/me", response_model=DeleteAccountResponse)
def delete_current_user(
    request: DeleteAccountRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """注销当前用户账户

    - 需要密码确认
    - 需要输入"DELETE"确认
    - 软删除（设置is_active=False）
    """
    user_service = UserService(db)

    success, error = user_service.delete_user(
        user_id=current_user.id,
        password=request.password,
        confirmation=request.confirmation
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return DeleteAccountResponse()


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """修改密码

    - 需要提供旧密码
    - 修改后会清除所有设备的登录状态（需要重新登录）
    """
    user_service = UserService(db)

    success, error = user_service.change_password(
        user_id=current_user.id,
        old_password=request.old_password,
        new_password=request.new_password
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return ChangePasswordResponse()


@router.get("/preferences", response_model=UserPreferencesResponse)
def get_user_preferences(
    current_user: User = Depends(get_current_active_user)
):
    """获取用户偏好设置

    - 返回用户的偏好设置JSON对象
    """
    return UserPreferencesResponse(
        preferences=current_user.preferences or {}
    )


@router.put("/preferences", response_model=UserPreferencesResponse)
def update_user_preferences(
    request: UserPreferencesUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """更新用户偏好设置

    - 提供完整的偏好设置JSON对象
    - 会覆盖原有设置
    """
    user_service = UserService(db)

    updated_user = user_service.update_preferences(
        user_id=current_user.id,
        preferences=request.preferences
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="更新失败"
        )

    return UserPreferencesResponse(
        preferences=updated_user.preferences or {}
    )

