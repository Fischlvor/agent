"""聊天相关的HTTP端点"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.schemas.chat import (
    AIModelResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
    MessageUpdate,
    SessionCreate,
    SessionListResponse,
    SessionResponse,
    SessionUpdate,
)
from app.services.chat_service import ChatService

LOGGER = logging.getLogger(__name__)

router = APIRouter()


# ============ 模型管理 ============

@router.get("/models", response_model=list[AIModelResponse])
def get_models(
    only_active: bool = Query(True, description="只返回激活的模型"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_active_user)
):
    """获取可用的AI模型列表

    Args:
        only_active: 是否只返回激活的模型
        db: 数据库会话
        _: 当前用户（用于权限验证）

    Returns:
        模型列表
    """
    chat_service = ChatService(db)
    models = chat_service.get_models(only_active=only_active)
    return models


# ============ 会话管理 ============

@router.post("/sessions", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
def create_session(
    request: SessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """创建新会话

    Args:
        request: 创建会话请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的会话对象
    """
    chat_service = ChatService(db)
    session = chat_service.create_session(
        user=current_user,
        title=request.title,
        ai_model=request.ai_model,
        system_prompt=request.system_prompt,
        temperature=request.temperature,
        max_tokens=request.max_tokens
    )
    return chat_service.enrich_session_with_context_info(session)


@router.get("/sessions", response_model=SessionListResponse)
def get_sessions(
    cursor: Optional[datetime] = Query(None, description="游标（last_activity_at）"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取会话列表（游标分页）

    Args:
        cursor: 游标（last_activity_at 时间戳）
        limit: 每页数量
        db: 数据库会话
        current_user: 当前用户

    Returns:
        会话列表和分页信息
    """
    chat_service = ChatService(db)
    sessions, next_cursor, has_more = chat_service.get_sessions(
        user=current_user,
        cursor=cursor,
        limit=limit
    )

    # ✅ 为每个会话添加上下文使用信息
    enriched_sessions = [
        chat_service.enrich_session_with_context_info(session)
        for session in sessions
    ]

    return SessionListResponse(
        sessions=enriched_sessions,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取单个会话详情

    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        会话对象
    """
    chat_service = ChatService(db)
    session = chat_service.get_session(session_id, current_user)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    # ✅ 添加上下文使用信息
    return chat_service.enrich_session_with_context_info(session)


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: str,
    request: SessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """更新会话

    Args:
        session_id: 会话ID
        request: 更新请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        更新后的会话对象
    """
    chat_service = ChatService(db)
    session = chat_service.update_session(
        session_id=session_id,
        user=current_user,
        **request.model_dump(exclude_unset=True)
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )
    return chat_service.enrich_session_with_context_info(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除会话

    Args:
        session_id: 会话ID
        db: 数据库会话
        current_user: 当前用户
    """
    chat_service = ChatService(db)
    success = chat_service.delete_session(session_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="会话不存在"
        )


# ============ 消息管理 ============

@router.post("/sessions/{session_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    session_id: str,
    request: MessageCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """发送消息到指定会话（HTTP POST），响应通过 WebSocket 流式返回

    Args:
        session_id: 会话ID
        request: 消息创建请求
        background_tasks: 后台任务
        db: 数据库会话
        current_user: 当前用户

    Returns:
        创建的用户消息对象（AI响应会通过WebSocket推送）
    """
    from app.api.endpoints.chat_ws import manager

    chat_service = ChatService(db)
    user_id = str(current_user.id)

    # 创建用户消息
    user_message = chat_service.create_user_message(
        session_id=session_id,
        user=current_user,
        content=request.content,
        model_id=request.model_id,
        parent_message_id=request.parent_message_id
    )

    # 后台任务：生成AI响应并通过WebSocket推送
    background_tasks.add_task(
        _generate_and_push_response,
        user_id=user_id,
        session_id=session_id,
        user=current_user,
        content=request.content,
        model_id=request.model_id
    )

    return user_message


async def _generate_and_push_response(
    user_id: str,
    session_id: str,
    user: User,
    content: str,
    model_id: Optional[str] = None
):
    """后台任务：生成响应并推送到WebSocket

    Args:
        user_id: 用户ID
        session_id: 会话ID
        user: 用户对象
        content: 消息内容
        model_id: 模型ID
    """
    from app.api.endpoints.chat_ws import manager  # pylint: disable=import-outside-toplevel
    from app.db.session import SESSION_LOCAL  # pylint: disable=import-outside-toplevel

    # 创建新的数据库会话（后台任务需要独立的会话）
    db = SESSION_LOCAL()
    try:
        chat_service = ChatService(db)

        # 清除停止标志
        manager.clear_stop_generation(user_id, str(session_id))

        # 流式生成并推送
        async for chunk in chat_service.send_message_streaming(
            session_id=session_id,
            user=user,
            content=content,
            model_id=model_id,
            skip_user_message=True  # 用户消息已经创建了
        ):
            # 检查停止标志
            if manager.check_stop_generation(user_id, str(session_id)):
                await manager.send_message(user_id, {
                    "type": "info",
                    "message": "已停止生成"
                })
                break

            # 检查连接是否仍然活跃
            if user_id not in manager.active_connections:
                break

            # 通过WebSocket推送
            await manager.send_message(user_id, chunk)

    except Exception as e:
        LOGGER.error("生成响应失败: %s", str(e), exc_info=True)
        # 错误也推送到前端
        try:
            await manager.send_message(user_id, {
                "type": "error",
                "error": str(e)
            })
        except Exception:
            LOGGER.error("推送错误消息失败", exc_info=True)
    finally:
        # 清除停止标志
        manager.clear_stop_generation(user_id, str(session_id))
        db.close()


@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
def get_messages(
    session_id: str,
    limit: int = Query(50, ge=1, le=200, description="消息数量限制"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取会话的消息历史

    Args:
        session_id: 会话ID
        limit: 消息数量限制
        db: 数据库会话
        current_user: 当前用户

    Returns:
        消息列表
    """
    chat_service = ChatService(db)
    messages = chat_service.get_messages(session_id, current_user, limit=limit)
    return MessageListResponse(
        messages=messages,
        total=len(messages)
    )


@router.patch("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def edit_message(
    message_id: str,
    request: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """编辑消息（删除原消息及后续所有回复，前端需再调用 sendMessage 发送新内容）

    Args:
        message_id: 消息ID
        request: 更新请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        204 No Content
    """
    chat_service = ChatService(db)
    success = chat_service.edit_message(
        message_id=message_id,
        user=current_user,
        new_content=request.content
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在或无权限"
        )


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """删除消息（软删除）

    Args:
        message_id: 消息ID
        db: 数据库会话
        current_user: 当前用户
    """
    chat_service = ChatService(db)
    success = chat_service.delete_message(message_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在或无权限"
        )

