"""分析统计API端点"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, Integer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.auth import get_current_active_user
from app.models.invocation import ModelInvocation, ToolInvocation
from app.models.user import User
from app.schemas.invocation import (
    InvocationStatsResponse,
    ModelInvocationResponse,
    ToolInvocationResponse,
    ToolUsageStatsResponse,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter()


# ============ LLM调用统计 ============

@router.get("/models/invocations", response_model=List[ModelInvocationResponse])
def get_model_invocations(
    message_id: Optional[str] = Query(None, description="消息ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取LLM调用记录列表

    Args:
        message_id: 过滤特定消息的调用
        session_id: 过滤特定会话的调用
        limit: 返回数量限制
        db: 数据库会话
        current_user: 当前用户

    Returns:
        LLM调用记录列表
    """
    query = db.query(ModelInvocation)

    if message_id:
        query = query.filter(ModelInvocation.message_id == message_id)

    if session_id:
        query = query.filter(ModelInvocation.session_id == session_id)

    # 按创建时间倒序
    invocations = query.order_by(ModelInvocation.created_at.desc()).limit(limit).all()

    return invocations


@router.get("/models/stats", response_model=InvocationStatsResponse)
def get_model_invocation_stats(
    session_id: Optional[str] = Query(None, description="会话ID"),
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取LLM调用统计

    Args:
        session_id: 过滤特定会话
        days: 统计最近N天的数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        统计结果
    """
    # 计算时间范围
    start_date = datetime.utcnow() - timedelta(days=days)

    # pylint: disable=not-callable
    query = db.query(
        func.count(ModelInvocation.id).label('total_invocations'),
        func.sum(ModelInvocation.total_tokens).label('total_tokens'),
        func.avg(ModelInvocation.duration_ms).label('avg_duration_ms'),
        func.sum(ModelInvocation.duration_ms).label('total_duration_ms'),
    ).filter(ModelInvocation.created_at >= start_date)
    # pylint: enable=not-callable

    if session_id:
        query = query.filter(ModelInvocation.session_id == session_id)

    result = query.first()

    return InvocationStatsResponse(
        total_invocations=result.total_invocations or 0,
        total_tokens=result.total_tokens or 0,
        avg_duration_ms=float(result.avg_duration_ms or 0),
        total_duration_ms=int(result.total_duration_ms or 0),
    )


# ============ 工具调用统计 ============

@router.get("/tools/invocations", response_model=List[ToolInvocationResponse])
def get_tool_invocations(
    message_id: Optional[str] = Query(None, description="消息ID"),
    session_id: Optional[str] = Query(None, description="会话ID"),
    tool_name: Optional[str] = Query(None, description="工具名称"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取工具调用记录列表

    Args:
        message_id: 过滤特定消息的调用
        session_id: 过滤特定会话的调用
        tool_name: 过滤特定工具
        limit: 返回数量限制
        db: 数据库会话
        current_user: 当前用户

    Returns:
        工具调用记录列表
    """
    query = db.query(ToolInvocation)

    if message_id:
        query = query.filter(ToolInvocation.message_id == message_id)

    if session_id:
        query = query.filter(ToolInvocation.session_id == session_id)

    if tool_name:
        query = query.filter(ToolInvocation.tool_name == tool_name)

    # 按创建时间倒序
    invocations = query.order_by(ToolInvocation.created_at.desc()).limit(limit).all()

    return invocations


@router.get("/tools/usage", response_model=List[ToolUsageStatsResponse])
def get_tool_usage_stats(
    session_id: Optional[str] = Query(None, description="会话ID"),
    days: int = Query(7, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取工具使用统计

    按工具分组统计调用次数、成功率、缓存命中率等

    Args:
        session_id: 过滤特定会话
        days: 统计最近N天的数据
        db: 数据库会话
        current_user: 当前用户

    Returns:
        各工具的统计结果列表
    """
    # 计算时间范围
    start_date = datetime.utcnow() - timedelta(days=days)

    # pylint: disable=not-callable
    query = db.query(
        ToolInvocation.tool_name,
        func.count(ToolInvocation.id).label('total_calls'),
        func.sum(func.cast(ToolInvocation.status == 'success', Integer)).label('success_count'),
        func.sum(func.cast(ToolInvocation.status == 'error', Integer)).label('error_count'),
        func.sum(func.cast(ToolInvocation.cache_hit == True, Integer)).label('cached_count'),  # noqa: E712
        func.avg(ToolInvocation.duration_ms).label('avg_duration_ms'),
    ).filter(ToolInvocation.created_at >= start_date)
    # pylint: enable=not-callable

    if session_id:
        query = query.filter(ToolInvocation.session_id == session_id)

    results = query.group_by(ToolInvocation.tool_name).all()

    # 计算百分比
    stats = []
    for result in results:
        total = result.total_calls
        success_rate = (result.success_count / total * 100) if total > 0 else 0
        cache_hit_rate = (result.cached_count / total * 100) if total > 0 else 0

        stats.append(ToolUsageStatsResponse(
            tool_name=result.tool_name,
            total_calls=result.total_calls,
            success_count=result.success_count or 0,
            error_count=result.error_count or 0,
            cached_count=result.cached_count or 0,
            success_rate=round(success_rate, 2),
            cache_hit_rate=round(cache_hit_rate, 2),
            avg_duration_ms=float(result.avg_duration_ms or 0),
        ))

    # 按调用次数倒序
    stats.sort(key=lambda x: x.total_calls, reverse=True)

    return stats


# ============ 综合统计 ============

@router.get("/messages/{message_id}/invocations")
def get_message_invocations(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取某条消息的所有调用记录

    包括LLM调用和工具调用

    Args:
        message_id: 消息ID
        db: 数据库会话
        current_user: 当前用户

    Returns:
        包含LLM和工具调用的完整记录
    """
    # 获取LLM调用
    model_invocations = db.query(ModelInvocation).filter(
        ModelInvocation.message_id == message_id
    ).order_by(ModelInvocation.sequence_number).all()

    # 获取工具调用
    tool_invocations = db.query(ToolInvocation).filter(
        ToolInvocation.message_id == message_id
    ).order_by(ToolInvocation.sequence_number).all()

    return {
        "message_id": str(message_id),
        "model_invocations": [
            ModelInvocationResponse.model_validate(inv) for inv in model_invocations
        ],
        "tool_invocations": [
            ToolInvocationResponse.model_validate(inv) for inv in tool_invocations
        ],
        "summary": {
            "total_llm_calls": len(model_invocations),
            "total_tool_calls": len(tool_invocations),
            "total_tokens": sum(inv.total_tokens for inv in model_invocations),
            "total_duration_ms": sum(
                (inv.duration_ms or 0 for inv in model_invocations),
                start=0
            ) + sum(
                (inv.duration_ms or 0 for inv in tool_invocations),
                start=0
            ),
        }
    }

