"""WebSocket端点，处理实时聊天"""

import asyncio
import json
import logging
from typing import Dict
from uuid import uuid4

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.db.session import get_db, SESSION_LOCAL
from app.middleware.auth import get_current_user_ws  # noqa: E402
from app.services.chat_service import ChatService
from app.constants.events import EventType

LOGGER = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, WebSocket] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}
        self.stop_generation_flags: Dict[str, bool] = {}  # ✅ 停止生成标志

    async def connect(self, user_id: str, websocket: WebSocket):
        """建立WebSocket连接

        Args:
            user_id: 用户ID
            websocket: WebSocket对象
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket

        # 启动心跳任务
        self.heartbeat_tasks[user_id] = asyncio.create_task(
            self._heartbeat(user_id, websocket)
        )

    async def disconnect(self, user_id: str):
        """断开WebSocket连接

        Args:
            user_id: 用户ID
        """
        # 取消心跳任务
        if user_id in self.heartbeat_tasks:
            self.heartbeat_tasks[user_id].cancel()
            del self.heartbeat_tasks[user_id]

        # 移除连接
        if user_id in self.active_connections:
            del self.active_connections[user_id]

    async def send_message(self, user_id: str, message: dict):
        """向指定用户发送消息

        Args:
            user_id: 用户ID
            message: 消息字典
        """
        if user_id in self.active_connections:
            websocket = self.active_connections[user_id]
            try:
                await websocket.send_json(message)
            except Exception as e:
                LOGGER.error("向用户 %s 发送消息失败: %s", user_id, str(e))
                # 发送失败，断开连接
                await self.disconnect(user_id)
                raise

    async def notify_document_status(self, user_id: str, kb_id: int, doc_id: int, status: str, error_msg: str = None):
        """通知文档状态更新（统一格式）

        Args:
            user_id: 用户ID
            kb_id: 知识库ID
            doc_id: 文档ID
            status: 文档状态 (pending/processing/completed/failed)
            error_msg: 错误信息（可选）
        """
        # 使用统一的WebSocket消息格式
        event_data = {
            "kb_id": kb_id,
            "doc_id": doc_id,
            "status": status,
            "error_msg": error_msg
        }

        message = {
            "event_type": EventType.DOCUMENT_STATUS_UPDATE,
            "event_id": str(uuid4()),  # 使用UUID作为事件ID
            "event_data": json.dumps(event_data, ensure_ascii=False)
        }

        if user_id in self.active_connections:
            try:
                await self.send_message(user_id, message)
                LOGGER.info(f"通知用户 {user_id} 文档 {doc_id} 状态更新: {status}")
            except Exception as e:
                LOGGER.warning(f"通知文档状态失败: {e}")

    async def _heartbeat(self, user_id: str, websocket: WebSocket):
        """心跳检测

        Args:
            user_id: 用户ID
            websocket: WebSocket对象
        """
        try:
            while True:
                await asyncio.sleep(30)  # 每30秒发送一次心跳
                await websocket.send_json({"type": "ping"})
        except asyncio.CancelledError:
            LOGGER.debug("用户 %s 心跳任务被取消", user_id)
        except Exception:
            LOGGER.exception("用户 %s 心跳任务异常", user_id)
            await self.disconnect(user_id)

    def set_stop_generation(self, user_id: str, session_id: str):
        """设置停止生成标志

        Args:
            user_id: 用户ID
            session_id: 会话ID
        """
        key = f"{user_id}:{session_id}"
        self.stop_generation_flags[key] = True

    def check_stop_generation(self, user_id: str, session_id: str) -> bool:
        """检查是否需要停止生成

        Args:
            user_id: 用户ID
            session_id: 会话ID

        Returns:
            True表示需要停止
        """
        key = f"{user_id}:{session_id}"
        return self.stop_generation_flags.get(key, False)

    def clear_stop_generation(self, user_id: str, session_id: str):
        """清除停止生成标志

        Args:
            user_id: 用户ID
            session_id: 会话ID
        """
        key = f"{user_id}:{session_id}"
        if key in self.stop_generation_flags:
            del self.stop_generation_flags[key]


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/chat")
async def websocket_chat_endpoint(
    websocket: WebSocket,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket聊天端点

    Args:
        websocket: WebSocket连接
        token: JWT token（从查询参数获取）
        db: 数据库会话（仅用于身份验证）
    """
    user = None
    user_id = None

    try:
        # ✅ 验证用户身份（使用临时数据库会话）
        user = await get_current_user_ws(token, db)
        user_id = str(user.id)

        # 建立连接
        await manager.connect(user_id, websocket)

        # 发送欢迎消息
        await manager.send_message(user_id, {
            "type": "connected",
            "message": "WebSocket连接成功"
        })

        # 监听客户端消息
        while True:
            try:
                # 接收消息
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type")

                # 处理不同类型的消息
                if msg_type == "ping":
                    # 心跳响应
                    await manager.send_message(user_id, {"type": "pong"})

                elif msg_type == "send_message":
                    # ⚠️ 已废弃：请使用 POST /api/v1/chat/sessions/{session_id}/messages
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": "send_message 已废弃，请使用 POST /api/v1/chat/sessions/{session_id}/messages"
                    })

                elif msg_type == "stop_generation":
                    # ✅ 实现停止生成逻辑
                    session_id = message.get("session_id")
                    if session_id:
                        manager.set_stop_generation(user_id, session_id)
                        await manager.send_message(user_id, {
                            "type": "info",
                            "message": "正在停止生成..."
                        })
                    else:
                        await manager.send_message(user_id, {
                            "type": "error",
                            "error": "缺少session_id参数"
                        })

                else:
                    # 未知消息类型
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": f"未知的消息类型: {msg_type}"
                    })

            except WebSocketDisconnect:
                # WebSocket正常断开，退出循环
                break
            except RuntimeError as e:
                # 处理 "Cannot call 'receive' once a disconnect message has been received" 错误
                if "disconnect" in str(e).lower():
                    break
                else:
                    LOGGER.exception("用户 %s 运行时错误", user_id)
                    break
            except json.JSONDecodeError:
                LOGGER.warning("用户 %s 发送了无效的JSON: %s", user_id, data)
                try:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": "无效的JSON格式"
                    })
                except Exception:
                    # 发送失败，说明连接已断开
                    break
            except ValueError as e:
                LOGGER.warning("用户 %s 消息值错误: %s", user_id, str(e))
                try:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": str(e)
                    })
                except Exception:
                    break
            except Exception as e:
                LOGGER.exception("用户 %s 处理消息时出错", user_id)
                try:
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": "处理消息时出错，请稍后重试"
                    })
                except Exception:
                    # 发送失败，说明连接已断开
                    break

    except WebSocketDisconnect:
        LOGGER.info("用户 %s 主动断开连接", user_id)
    except Exception:
        LOGGER.exception("WebSocket连接异常")
        try:
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        except Exception:
            pass
    finally:
        # 清理连接
        if user_id:
            await manager.disconnect(user_id)

