"""聊天相关的HTTP端点"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_active_user
from app.models.user import User
from app.schemas.chat import (
    AIModelResponse,
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
    return session


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
    return SessionListResponse(
        sessions=sessions,
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
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
    return session


@router.patch("/sessions/{session_id}", response_model=SessionResponse)
def update_session(
    session_id: UUID,
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
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: UUID,
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

@router.get("/sessions/{session_id}/messages", response_model=MessageListResponse)
def get_messages(
    session_id: UUID,
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


@router.patch("/messages/{message_id}", response_model=MessageResponse)
def edit_message(
    message_id: UUID,
    request: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """编辑消息（ChatGPT方式：删除后续所有回复）

    Args:
        message_id: 消息ID
        request: 更新请求
        db: 数据库会话
        current_user: 当前用户

    Returns:
        编辑后的消息对象
    """
    chat_service = ChatService(db)
    message = chat_service.edit_message(
        message_id=message_id,
        user=current_user,
        new_content=request.content
    )
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="消息不存在或无权限"
        )
    return message


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(
    message_id: UUID,
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

