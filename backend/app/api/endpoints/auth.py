"""SSO认证服务API端点"""

from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from sqlalchemy.orm import Session

from app.core.config import SETTINGS
from app.db.session import get_db
from app.schemas.auth import (
    EmailCodeLoginRequest,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    LoginResponse,
    LogoutResponse,
    PasswordLoginRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    SendLoginCodeRequest,
    SendLoginCodeResponse,
    VerifyEmailResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/sso/auth", tags=["SSO认证"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(
    request: RegisterRequest,
    db: Session = Depends(get_db)
):
    """用户注册

    - 创建新用户账户
    - 发送邮箱验证邮件
    - 用户需要验证邮箱后才能登录
    """
    auth_service = AuthService(db)

    # 检查用户名是否已存在
    if auth_service.user_service.get_user_by_username(request.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已被使用"
        )

    # 检查邮箱是否已存在
    if auth_service.user_service.get_user_by_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已被注册"
        )

    # 注册用户
    result = auth_service.register_user(
        username=request.username,
        email=request.email,
        password=request.password,
        full_name=request.full_name
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="注册失败，请稍后重试"
        )

    user, email_sent = result

    # 检查邮件是否发送成功
    if not email_sent:
        # 即使发送失败，用户也已注册，提示用户可以重新发送
        return RegisterResponse(
            message="注册成功，但验证邮件发送失败，请重新发送验证邮件",
            user_id=user.id,
            email=user.email
        )

    return RegisterResponse(
        user_id=user.id,
        email=user.email
    )


@router.get("/verify-email", response_model=VerifyEmailResponse)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """验证邮箱

    - 用户点击邮件中的验证链接
    - 激活账户，允许登录
    """
    auth_service = AuthService(db)

    try:
        user = auth_service.verify_email(token)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="验证失败，token无效或已过期"
            )

        return VerifyEmailResponse(user_id=user.id)
    except ValueError as e:
        error_msg = str(e)
        # 如果是"邮箱已验证"的错误，返回友好提示
        if "已验证" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该邮箱已经验证过了，无需重复验证，请直接登录"
            ) from e
        # 其他错误
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        ) from e


@router.post("/resend-verification", response_model=ResendVerificationResponse)
def resend_verification(
    request: ResendVerificationRequest,
    db: Session = Depends(get_db)
):
    """重新发送验证邮件

    - 用户未收到验证邮件时使用
    """
    auth_service = AuthService(db)

    user = auth_service.user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="邮箱已验证，无需重复验证"
        )

    success = auth_service.resend_verification_email(request.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送邮件失败，请稍后重试"
        )

    return ResendVerificationResponse()


@router.post("/send-login-code", response_model=SendLoginCodeResponse)
def send_login_code(
    request: SendLoginCodeRequest,
    db: Session = Depends(get_db)
):
    """发送登录验证码

    - 发送6位验证码到用户邮箱
    - 验证码5分钟有效
    """
    auth_service = AuthService(db)

    user = auth_service.user_service.get_user_by_email(request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="用户不存在"
        )

    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="邮箱未验证，请先验证邮箱"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用"
        )

    success = auth_service.send_login_code(request.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送验证码失败，请稍后重试"
        )

    return SendLoginCodeResponse()


@router.post("/login/password", response_model=LoginResponse)
def login_with_password(
    response: Response,
    request: PasswordLoginRequest,
    db: Session = Depends(get_db)
):
    """密码登录

    - 用户名/邮箱 + 密码
    - 返回Access Token（JWT）
    - 设置Refresh Token到HttpOnly Cookie
    """
    auth_service = AuthService(db)

    try:
        user, access_token, refresh_token = auth_service.password_login(
            login=request.login,
            password=request.password
        )
    except ValueError as e:
        error_msg = str(e)
        # 区分不同类型的错误
        if "邮箱未验证" in error_msg or "账户已被禁用" in error_msg:
            # 用户身份已确认，但因状态问题被拒绝 → 403
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=error_msg
            ) from e
        else:
            # 用户身份验证失败（密码错误、用户不存在） → 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=error_msg
            ) from e

    # 设置Refresh Token到HttpOnly Cookie
    # Secure=False for local development (http), True for production (https)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # 生产环境改为True
        samesite="lax",
        max_age=SETTINGS.refresh_token_expire_days * 24 * 60 * 60,  # 7天
        path="/api/v1/sso/auth"  # 限制Cookie作用域
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=SETTINGS.access_token_expire_minutes * 60,
        user=user.to_dict()
    )


@router.post("/login/email-code", response_model=LoginResponse)
def login_with_email_code(
    response: Response,
    request: EmailCodeLoginRequest,
    db: Session = Depends(get_db)
):
    """邮箱验证码登录

    - 邮箱 + 6位验证码
    - 返回Access Token（JWT）
    - 设置Refresh Token到HttpOnly Cookie
    """
    auth_service = AuthService(db)

    try:
        user, access_token, refresh_token = auth_service.email_code_login(
            email=request.email,
            code=request.code
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e

    # 设置Refresh Token到HttpOnly Cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,  # 生产环境改为True
        samesite="lax",
        max_age=SETTINGS.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/sso/auth"
    )

    return LoginResponse(
        access_token=access_token,
        expires_in=SETTINGS.access_token_expire_minutes * 60,
        user=user.to_dict()
    )


@router.post("/refresh", response_model=RefreshTokenResponse)
def refresh_token_endpoint(
    response: Response,
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db)
):
    """刷新Access Token

    - 使用Refresh Token获取新的Access Token
    - 返回新的Access Token和新的Refresh Token
    """
    auth_service = AuthService(db)

    # ✅ refresh_token 自动从 Cookie 中读取
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少Refresh Token"
        )

    try:
        result = auth_service.refresh_access_token(refresh_token)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh Token无效或已过期"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        ) from e

    new_access_token, new_refresh_token, _ = result

    # 设置新的Refresh Token到Cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=False,  # 生产环境改为True
        samesite="lax",
        max_age=SETTINGS.refresh_token_expire_days * 24 * 60 * 60,
        path="/api/v1/sso/auth"
    )

    return RefreshTokenResponse(
        access_token=new_access_token,
        expires_in=SETTINGS.access_token_expire_minutes * 60
    )


@router.post("/logout", response_model=LogoutResponse)
def logout(
    response: Response,
    refresh_token: str = None,
    db: Session = Depends(get_db)
):
    """用户登出

    - 删除Refresh Token
    - 清除Cookie
    """
    auth_service = AuthService(db)

    if refresh_token:
        auth_service.logout(refresh_token)

    # 清除Cookie
    response.delete_cookie(
        key="refresh_token",
        path="/api/v1/sso/auth"
    )

    return LogoutResponse()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    """忘记密码

    - 发送密码重置邮件
    - 邮件中包含重置链接
    """
    auth_service = AuthService(db)

    user = auth_service.user_service.get_user_by_email(request.email)
    if not user:
        # 为了安全，即使用户不存在也返回成功（防止邮箱枚举）
        return ForgotPasswordResponse()

    success = auth_service.forgot_password(request.email)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="发送邮件失败，请稍后重试"
        )

    return ForgotPasswordResponse()


@router.post("/reset-password", response_model=ResetPasswordResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """重置密码

    - 使用密码重置token设置新密码
    """
    auth_service = AuthService(db)

    success = auth_service.reset_password(request.token, request.new_password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="重置失败，token无效或已过期"
        )

    return ResetPasswordResponse()

