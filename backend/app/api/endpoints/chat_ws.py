"""WebSocket端点，处理实时聊天"""

import asyncio
import json
import logging
from typing import Dict
from uuid import UUID

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.db.session import get_db, SESSION_LOCAL
from app.middleware.auth import get_current_user_ws  # noqa: E402
from app.services.chat_service import ChatService

LOGGER = logging.getLogger(__name__)

router = APIRouter()


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        """初始化连接管理器"""
        self.active_connections: Dict[str, WebSocket] = {}
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        """建立WebSocket连接

        Args:
            user_id: 用户ID
            websocket: WebSocket对象
        """
        await websocket.accept()
        self.active_connections[user_id] = websocket
        LOGGER.info("用户 %s 建立WebSocket连接", user_id)

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
            LOGGER.info("用户 %s 断开WebSocket连接", user_id)

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

                LOGGER.info("收到用户 %s 的消息: %s", user_id, msg_type)

                # 处理不同类型的消息
                if msg_type == "ping":
                    # 心跳响应
                    await manager.send_message(user_id, {"type": "pong"})

                elif msg_type == "send_message":
                    # 发送聊天消息
                    session_id = UUID(message.get("session_id"))
                    content = message.get("content")
                    model_id = message.get("model_id")
                    skip_user_message = message.get("skip_user_message", False)  # ✅ 支持跳过创建用户消息
                    edited_message_id = message.get("edited_message_id")  # ✅ 编辑的消息ID

                    if not content:
                        await manager.send_message(user_id, {
                            "type": "error",
                            "error": "消息内容不能为空"
                        })
                        continue

                    # ✅ 每次处理消息时创建新的数据库会话（避免长事务）
                    db_session = SESSION_LOCAL()
                    try:
                        chat_service = ChatService(db_session)

                        # 流式生成回复（带超时和错误处理）
                        async for chunk in chat_service.send_message_streaming(
                            session_id=session_id,
                            user=user,
                            content=content,
                            model_id=model_id,
                            skip_user_message=skip_user_message,  # ✅ 传递参数
                            edited_message_id=UUID(edited_message_id) if edited_message_id else None  # ✅ 传递编辑的消息ID
                        ):
                            # 检查连接是否仍然活跃
                            if user_id not in manager.active_connections:
                                LOGGER.warning("用户 %s 连接已断开，停止发送消息", user_id)
                                break
                            await manager.send_message(user_id, chunk)
                    except asyncio.TimeoutError:
                        LOGGER.error("用户 %s 消息处理超时", user_id)
                        await manager.send_message(user_id, {
                            "type": "error",
                            "error": "消息处理超时，请稍后重试"
                        })
                    except Exception as stream_error:
                        LOGGER.exception("用户 %s 流式生成消息时出错", user_id)
                        await manager.send_message(user_id, {
                            "type": "error",
                            "error": f"生成消息时出错: {str(stream_error)}"
                        })
                    finally:
                        # ✅ 确保数据库会话被正确关闭
                        db_session.close()

                elif msg_type == "stop_generation":
                    # TODO: 实现停止生成逻辑
                    await manager.send_message(user_id, {
                        "type": "info",
                        "message": "停止生成功能即将支持"
                    })

                else:
                    # 未知消息类型
                    await manager.send_message(user_id, {
                        "type": "error",
                        "error": f"未知的消息类型: {msg_type}"
                    })

            except WebSocketDisconnect:
                # WebSocket正常断开，退出循环
                LOGGER.info("用户 %s WebSocket连接断开", user_id)
                break
            except RuntimeError as e:
                # 处理 "Cannot call 'receive' once a disconnect message has been received" 错误
                if "disconnect" in str(e).lower():
                    LOGGER.info("用户 %s 连接已断开（RuntimeError）", user_id)
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

