"""聊天服务层，处理会话和消息的业务逻辑"""

import json
import logging
import re
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional, Tuple, Any
from uuid import UUID, uuid4

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.ai.agent_service import AgentService
from app.ai.factory import FACTORY
from app.constants import EventType, ContentType, MessageStatus
from app.models.ai_model import AIModel
from app.models.chat import ChatMessage
from app.models.session import ChatSession
from app.models.user import User

LOGGER = logging.getLogger(__name__)


class ChatService:
    """聊天服务"""

    def __init__(self, db: Session):
        """初始化聊天服务

        Args:
            db: 数据库会话
        """
        self.db = db

    @staticmethod
    def _get_next_event_id(
        event_type: int,
        current_type: Optional[int],
        current_id: int
    ) -> Tuple[int, int]:
        """获取下一个事件ID（事件类型变化时归零）

        Args:
            event_type: 新的事件类型
            current_type: 当前事件类型
            current_id: 当前事件ID

        Returns:
            (新的event_id, 新的current_type)
        """
        if current_type is None or event_type != current_type:
            # 事件类型变化，ID归零
            return 0, event_type
        else:
            # 同类型事件，ID递增
            return current_id + 1, event_type

    @staticmethod
    def _wrap_ws_message(
        event_data: Dict[str, Any],
        event_id: int,
        event_type: int
    ) -> Dict[str, Any]:
        """包装 WebSocket 消息为标准格式

        Args:
            event_data: 事件数据
            event_id: 事件序列号
            event_type: 事件类型代码

        Returns:
            包装后的消息
        """
        return {
            "event_data": json.dumps(event_data, ensure_ascii=False),
            "event_id": str(event_id),
            "event_type": event_type
        }

    # ============ 模型管理 ============

    def get_models(self, only_active: bool = True) -> List[AIModel]:
        """获取可用模型列表

        Args:
            only_active: 是否只返回激活的模型

        Returns:
            模型列表
        """
        query = self.db.query(AIModel)
        if only_active:
            query = query.filter(AIModel.is_active == True)  # noqa: E712
        return query.order_by(AIModel.display_order).all()

    def get_model_by_id(self, model_id: str) -> Optional[AIModel]:
        """根据model_id获取模型配置

        Args:
            model_id: 模型ID

        Returns:
            模型对象，如果不存在则返回None
        """
        return self.db.query(AIModel).filter(
            and_(
                AIModel.model_id == model_id,
                AIModel.is_active == True  # noqa: E712
            )
        ).first()

    # ============ 会话管理 ============

    def create_session(
        self,
        user: User,
        title: Optional[str] = None,
        ai_model: str = "qwen3:8b",
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4000,
    ) -> ChatSession:
        """创建新会话

        Args:
            user: 用户对象
            title: 会话标题
            ai_model: AI模型ID
            system_prompt: 系统提示词
            temperature: 温度参数
            max_tokens: 最大令牌数

        Returns:
            创建的会话对象
        """
        session = ChatSession(
            session_id=str(uuid4()),
            user_id=user.id,
            title=title or "新对话",
            status="active",
            ai_model=ai_model,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            last_activity_at=datetime.utcnow(),
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_sessions(
        self,
        user: User,
        cursor: Optional[datetime] = None,
        limit: int = 20
    ) -> Tuple[List[ChatSession], Optional[datetime], bool]:
        """获取用户的会话列表（游标分页）

        Args:
            user: 用户对象
            cursor: 游标（last_activity_at 时间戳）
            limit: 每页数量

        Returns:
            (会话列表, 下一页游标, 是否还有更多)
        """
        query = self.db.query(ChatSession).filter(
            ChatSession.user_id == user.id
        )

        if cursor:
            query = query.filter(ChatSession.last_activity_at < cursor)

        # 按最后活动时间倒序
        sessions = query.order_by(
            desc(ChatSession.last_activity_at)
        ).limit(limit + 1).all()

        has_more = len(sessions) > limit
        if has_more:
            sessions = sessions[:limit]

        next_cursor = sessions[-1].last_activity_at if sessions and has_more else None

        return sessions, next_cursor, has_more

    def get_session(self, session_id: UUID, user: User) -> Optional[ChatSession]:
        """获取单个会话

        Args:
            session_id: 会话ID
            user: 用户对象

        Returns:
            会话对象，如果不存在或不属于该用户则返回None
        """
        return self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == session_id,
                ChatSession.user_id == user.id
            )
        ).first()

    def update_session(
        self,
        session_id: UUID,
        user: User,
        **kwargs
    ) -> Optional[ChatSession]:
        """更新会话

        Args:
            session_id: 会话ID
            user: 用户对象
            **kwargs: 要更新的字段

        Returns:
            更新后的会话对象
        """
        session = self.get_session(session_id, user)
        if not session:
            return None

        for key, value in kwargs.items():
            if value is not None and hasattr(session, key):
                setattr(session, key, value)

        self.db.commit()
        self.db.refresh(session)
        return session

    def delete_session(self, session_id: UUID, user: User) -> bool:
        """删除会话

        Args:
            session_id: 会话ID
            user: 用户对象

        Returns:
            是否成功删除
        """
        session = self.get_session(session_id, user)
        if not session:
            return False

        self.db.delete(session)
        self.db.commit()
        return True

    # ============ 消息管理 ============

    def get_messages(
        self,
        session_id: UUID,
        user: User,
        limit: int = 50
    ) -> List[ChatMessage]:
        """获取会话的消息历史

        Args:
            session_id: 会话ID
            user: 用户对象
            limit: 消息数量限制

        Returns:
            消息列表
        """
        session = self.get_session(session_id, user)
        if not session:
            return []

        return self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False  # noqa: E712
            )
        ).order_by(ChatMessage.created_at).limit(limit).all()

    def create_message(
        self,
        session_id: UUID,
        role: str,
        content: str,
        **kwargs
    ) -> ChatMessage:
        """创建消息

        Args:
            session_id: 会话ID
            role: 角色（user/assistant/system/tool）
            content: 消息内容
            **kwargs: 其他字段

        Returns:
            创建的消息对象
        """
        message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            role=role,
            content=content,
            sent_at=datetime.utcnow(),
            status="sent",
            **kwargs
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)

        # 更新会话的最后活动时间和消息计数
        session = self.db.query(ChatSession).filter(
            ChatSession.id == session_id
        ).first()
        if session:
            session.last_activity_at = datetime.utcnow()
            session.message_count += 1
            if message.total_tokens:
                session.total_tokens += message.total_tokens
            self.db.commit()

        return message

    def edit_message(
        self,
        message_id: UUID,
        user: User,
        new_content: str
    ) -> Optional[ChatMessage]:
        """编辑消息（创建新消息，软删除原消息及后续所有回复）

        Args:
            message_id: 原消息ID
            user: 用户对象
            new_content: 新内容

        Returns:
            新创建的消息对象
        """
        original_message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()

        if not original_message:
            return None

        # 检查权限
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == original_message.session_id,
                ChatSession.user_id == user.id
            )
        ).first()

        if not session:
            return None

        # ✅ 1. 软删除原消息（保留审计历史）
        original_message.is_deleted = True

        # ✅ 2. 软删除该消息之后的所有消息（保留审计历史）
        later_messages = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == original_message.session_id,
                ChatMessage.created_at > original_message.created_at,
                ChatMessage.is_deleted == False  # 只处理未删除的消息
            )
        ).all()

        for msg in later_messages:
            msg.is_deleted = True

        # ✅ 3. 创建新消息（内容为编辑后的内容）
        now = datetime.utcnow()
        new_message = ChatMessage(
            message_id=str(uuid4()),
            session_id=original_message.session_id,
            parent_message_id=str(message_id),  # ✅ 记录父消息ID，可追踪编辑历史
            role=original_message.role,
            content=new_content,
            message_type=original_message.message_type,
            is_edited=True,  # ✅ 标记为编辑后的消息
            is_deleted=False,
            created_at=now,
            sent_at=now  # ✅ 设置发送时间
        )
        self.db.add(new_message)
        self.db.commit()
        self.db.refresh(new_message)

        # ✅ 4. 更新会话统计（只统计未删除的消息）
        session.message_count = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == original_message.session_id,
                ChatMessage.is_deleted == False
            )
        ).count()
        session.last_activity_at = datetime.utcnow()
        self.db.commit()

        return new_message

    def delete_message(self, message_id: UUID, user: User) -> bool:
        """删除消息（软删除）

        Args:
            message_id: 消息ID
            user: 用户对象

        Returns:
            是否成功删除
        """
        message = self.db.query(ChatMessage).filter(
            ChatMessage.id == message_id
        ).first()

        if not message:
            return False

        # 检查权限
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.id == message.session_id,
                ChatSession.user_id == user.id
            )
        ).first()

        if not session:
            return False

        message.is_deleted = True
        self.db.commit()
        return True

    # ============ AI对话 ============

    async def send_message_streaming(
        self,
        session_id: UUID,
        user: User,
        content: str,
        model_id: Optional[str] = None,
        skip_user_message: bool = False,
        edited_message_id: Optional[UUID] = None
    ) -> AsyncIterator[Dict]:
        """发送消息并流式返回AI回复

        Args:
            session_id: 会话ID
            user: 用户对象
            content: 消息内容
            model_id: 模型ID（可选，不指定则使用会话默认模型）
            skip_user_message: 是否跳过创建用户消息（用于编辑后重新生成）
            edited_message_id: 编辑的消息ID（用于追踪和验证）

        Yields:
            WebSocket消息字典
        """
        # ✅ 事件计数器：事件类型变化时归零
        event_id = 0
        current_event_type = None  # 跟踪当前事件类型
        message_index = 0
        error_message_id = str(uuid4())

        # 获取会话
        session = self.get_session(session_id, user)
        if not session:
            event_id, current_event_type = self._get_next_event_id(
                EventType.ERROR, current_event_type, event_id
            )
            yield self._wrap_ws_message(
                event_data={
                    "message_id": error_message_id,
                    "conversation_id": str(session_id),
                    "message": {
                        "id": str(uuid4()),
                        "content_type": ContentType.ERROR,
                        "content": json.dumps({"error": "会话不存在"})
                    },
                    "status": MessageStatus.ERROR,
                    "is_finish": True,
                    "message_index": message_index
                },
                event_id=event_id,
                event_type=EventType.ERROR
            )
            return

        # 确定使用的模型
        target_model_id = model_id or session.ai_model or "qwen3:8b"
        model_config = self.get_model_by_id(target_model_id)
        if not model_config:
            yield self._wrap_ws_message(
                event_data={
                    "message_id": error_message_id,
                    "conversation_id": str(session_id),
                    "message": {
                        "id": str(uuid4()),
                        "content_type": ContentType.ERROR,
                        "content": json.dumps({"error": f"模型 {target_model_id} 不存在或未激活"})
                    },
                    "status": MessageStatus.ERROR,
                    "is_finish": True,
                    "message_index": message_index
                },
                event_id=event_id,
                event_type=EventType.ERROR
            )
            return

        # 创建用户消息（保存到数据库）
        # ✅ 编辑重新生成时跳过创建新的用户消息
        if not skip_user_message:
            _user_message = self.create_message(
                session_id=session_id,
                role="user",
                content=content,
                message_type="text"
            )

        # 生成助手消息ID（用于整个对话回合）
        assistant_message_id = str(uuid4())

        # 发送开始消息
        event_id, current_event_type = self._get_next_event_id(
            EventType.MESSAGE_START, current_event_type, event_id
        )
        yield self._wrap_ws_message(
            event_data={
                "message_id": assistant_message_id,
                "conversation_id": str(session_id),
                "status": MessageStatus.PENDING,
                "message_index": message_index
            },
            event_id=event_id,
            event_type=EventType.MESSAGE_START
        )
        message_index += 1

        # 获取历史消息
        history_messages = self.get_messages(session_id, user, limit=20)

        # ✅ 根据是否跳过用户消息来决定如何处理历史
        if skip_user_message:
            # 编辑重新生成：使用全部历史（最后一条就是编辑后的用户消息）

            # ✅ 验证编辑的消息（用于追踪和日志）
            if edited_message_id and history_messages:
                last_message = history_messages[-1]
                # 验证最后一条消息是编辑后的新消息（parent_message_id 应该等于原消息ID）
                if last_message.parent_message_id and str(last_message.parent_message_id) == str(edited_message_id):
                    LOGGER.info(f"✅ 重新生成回复：基于编辑的消息 {edited_message_id} (新消息ID: {last_message.message_id})，新内容: {content[:50]}...")
                else:
                    LOGGER.warning(f"⚠️ 编辑消息ID验证失败：期望 parent_message_id={edited_message_id}，实际 message_id={last_message.message_id}, parent_message_id={last_message.parent_message_id}")

            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in history_messages
            ]
        else:
            # 正常发送：排除最后一条（刚创建的用户消息），然后添加当前内容
            messages = [
                {"role": msg.role, "content": msg.content}
                for msg in history_messages[:-1]
            ]
            messages.append({"role": "user", "content": content})

        # 创建AI客户端
        client = FACTORY.create_client(
            provider=model_config.provider,
            model_name=model_config.model_id,
            base_url=model_config.base_url
        )

        # 创建Agent服务
        agent = AgentService(client, debug=False)

        # 流式生成
        assistant_content = ""
        has_sent_thinking = False  # ✅ 是否已发送 thinking
        thinking_buffer = ""  # ✅ 累积的 thinking 内容
        last_sent_content_len = 0  # ✅ 记录已发送的 content 长度（用于多轮思考）
        current_thinking_id = None  # ✅ 当前正在进行的 thinking 块的 ID
        timeline = []  # ✅ 记录事件时间线（thinking、tool_call、content）
        start_time = datetime.utcnow()

        try:
            async for chunk in agent.run_streaming(
                messages=messages,
                system_prompt=session.system_prompt,
                tools=None  # TODO: 集成工具列表
            ):
                # 🐛 调试日志：打印原始 chunk
                LOGGER.debug(f"📦 Received chunk: type={chunk.get('type')}, content={chunk.get('content', '')[:100]}")

                if chunk["type"] == "content":
                    content_delta = chunk["content"]
                    assistant_content += content_delta

                    # 🐛 调试日志：打印累积的内容
                    LOGGER.debug(f"📝 Accumulated content length: {len(assistant_content)}, has <think>: {'<think>' in assistant_content}, has </think>: {'</think>' in assistant_content}")

                    # ✅ 检测和分离 thinking 内容（支持多轮思考，带开始/完成消息）
                    # 提取所有完整的 <think>...</think> 块
                    while "<think>" in assistant_content and "</think>" in assistant_content:
                        # 找到第一个完整的 thinking 块
                        match = re.search(r'<think>(.*?)</think>', assistant_content, re.DOTALL)
                        if match:
                            thinking_text = match.group(1).strip()
                            # ✅ 使用流式时的 ID，如果没有则生成新的
                            thinking_id = current_thinking_id if current_thinking_id else str(uuid4())

                            # 保存到时间线
                            if thinking_text:
                                timeline.append({
                                    "type": "thinking",
                                    "content": thinking_text,
                                    "thinking_id": thinking_id,
                                    "timestamp": datetime.utcnow().isoformat()
                                })

                                # ✅ 发送思考完成消息（只发送状态，不发送全量内容）
                                event_id, current_event_type = self._get_next_event_id(
                                    EventType.THINKING_COMPLETE, current_event_type, event_id
                                )
                                yield self._wrap_ws_message(
                                    event_data={
                                        "message_id": assistant_message_id,
                                        "conversation_id": str(session_id),
                                        "message": {
                                            "id": thinking_id,  # ✅ 现在使用流式时的 ID
                                            "content_type": ContentType.THINKING,
                                            "content": json.dumps({"finish_title": "已完成思考"})  # ✅ 对齐业界标准
                                        },
                                        "status": MessageStatus.COMPLETED,
                                        "is_finish": True,
                                        "message_index": message_index
                                    },
                                    event_id=event_id,
                                    event_type=EventType.THINKING_COMPLETE
                                )
                                message_index += 1

                            # 移除这个 thinking 块
                            assistant_content = assistant_content[:match.start()] + assistant_content[match.end():]
                            thinking_buffer = ""  # 清空 thinking buffer
                            current_thinking_id = None  # 清空当前 thinking ID
                        else:
                            break

                    # 处理未完成的 thinking（只有 <think> 没有 </think>）
                    if "<think>" in assistant_content and "</think>" not in assistant_content:
                        think_pos = assistant_content.find("<think>")
                        before_think = assistant_content[:think_pos]
                        current_thinking = assistant_content[think_pos + 7:]  # 跳过 "<think>"

                        # 先发送 thinking 之前的 content
                        if before_think and last_sent_content_len < len(before_think):
                            content_to_send = before_think[last_sent_content_len:]
                            last_sent_content_len = len(before_think)
                            if content_to_send:
                                content_id = str(uuid4())
                                event_id, current_event_type = self._get_next_event_id(
                                    EventType.MESSAGE_CONTENT, current_event_type, event_id
                                )
                                yield self._wrap_ws_message(
                                    event_data={
                                        "message_id": assistant_message_id,
                                        "conversation_id": str(session_id),
                                        "message": {
                                            "id": content_id,
                                            "content_type": ContentType.TEXT,
                                            "content": json.dumps({"text": content_to_send})  # ✅ 统一使用 text 字段
                                        },
                                        "status": MessageStatus.PENDING,
                                        "is_delta": True,
                                        "message_index": message_index
                                    },
                                    event_id=event_id,
                                    event_type=EventType.MESSAGE_CONTENT
                                )
                                message_index += 1

                        # ✅ 如果是新的 thinking 块，发送开始消息
                        if not current_thinking_id:
                            current_thinking_id = str(uuid4())
                            event_id, current_event_type = self._get_next_event_id(
                                EventType.THINKING_START, current_event_type, event_id
                            )
                            yield self._wrap_ws_message(
                                event_data={
                                    "message_id": assistant_message_id,
                                    "conversation_id": str(session_id),
                                    "message": {
                                        "id": current_thinking_id,
                                        "content_type": ContentType.THINKING,
                                        "content": json.dumps({"finish_title": "深度思考中"})  # ✅ 对齐业界标准
                                    },
                                    "status": MessageStatus.PENDING,
                                    "is_delta": True,
                                    "message_index": message_index
                                },
                                event_id=event_id,
                                event_type=EventType.THINKING_START
                            )
                            message_index += 1

                        # 流式发送 thinking delta
                        new_thinking_delta = current_thinking[len(thinking_buffer):]
                        thinking_buffer = current_thinking

                        if new_thinking_delta:
                            event_id, current_event_type = self._get_next_event_id(
                                EventType.THINKING_DELTA, current_event_type, event_id
                            )
                            yield self._wrap_ws_message(
                                event_data={
                                    "message_id": assistant_message_id,
                                    "conversation_id": str(session_id),
                                    "message": {
                                        "id": current_thinking_id,
                                        "content_type": ContentType.THINKING,
                                        "content": json.dumps({"text": new_thinking_delta})  # ✅ 统一使用 text 字段
                                    },
                                    "status": MessageStatus.PENDING,
                                    "is_delta": True,
                                    "message_index": message_index
                                },
                                event_id=event_id,
                                event_type=EventType.THINKING_DELTA
                            )
                            message_index += 1
                    else:
                        # 没有未完成的 thinking，发送普通 content delta
                        if assistant_content and last_sent_content_len < len(assistant_content):
                            content_to_send = assistant_content[last_sent_content_len:]
                            last_sent_content_len = len(assistant_content)
                            if content_to_send:
                                content_id = str(uuid4())
                                event_id, current_event_type = self._get_next_event_id(
                                    EventType.MESSAGE_CONTENT, current_event_type, event_id
                                )
                                yield self._wrap_ws_message(
                                    event_data={
                                        "message_id": assistant_message_id,
                                        "conversation_id": str(session_id),
                                        "message": {
                                            "id": content_id,
                                            "content_type": ContentType.TEXT,
                                            "content": json.dumps({"text": content_to_send})  # ✅ 统一使用 text 字段
                                        },
                                        "status": MessageStatus.PENDING,
                                        "is_delta": True,
                                        "message_index": message_index
                                    },
                                    event_id=event_id,
                                    event_type=EventType.MESSAGE_CONTENT
                                )
                                message_index += 1

                elif chunk["type"] == "tool_calls":
                    for tool_call in chunk.get("tool_calls", []):
                        tool_call_id = str(uuid4())
                        # ✅ 添加到时间线
                        timeline.append({
                            "type": "tool_call",
                            "tool_name": tool_call["function"]["name"],
                            "tool_args": tool_call["function"]["arguments"],
                            "tool_id": tool_call_id,
                            "status": "pending",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        event_id, current_event_type = self._get_next_event_id(
                            EventType.TOOL_CALL, current_event_type, event_id
                        )
                        yield self._wrap_ws_message(
                            event_data={
                                "message_id": assistant_message_id,
                                "conversation_id": str(session_id),
                                "message": {
                                    "id": tool_call_id,
                                    "content_type": ContentType.TOOL_CALL,
                                    "content": json.dumps({
                                        "name": tool_call["function"]["name"],
                                        "args": tool_call["function"]["arguments"]
                                    })
                                },
                                "status": MessageStatus.PENDING,
                                "message_index": message_index
                            },
                            event_id=event_id,
                            event_type=EventType.TOOL_CALL
                        )
                        message_index += 1

                elif chunk["type"] == "tool_result":
                    # ✅ 更新时间线中对应工具调用的结果
                    tool_result_id = None
                    for event in reversed(timeline):
                        if event["type"] == "tool_call" and event["tool_name"] == chunk["tool_name"] and event.get("status") == "pending":
                            event["result"] = chunk["result"]
                            event["status"] = "success"
                            tool_result_id = event.get("tool_id")
                            break

                    event_id, current_event_type = self._get_next_event_id(
                        EventType.TOOL_RESULT, current_event_type, event_id
                    )
                    yield self._wrap_ws_message(
                        event_data={
                            "message_id": assistant_message_id,
                            "conversation_id": str(session_id),
                            "message": {
                                "id": tool_result_id or str(uuid4()),
                                "content_type": ContentType.TOOL_RESULT,
                                "content": json.dumps({
                                    "name": chunk["tool_name"],
                                    "result": chunk["result"]
                                })
                            },
                            "status": MessageStatus.COMPLETED,
                            "message_index": message_index
                        },
                        event_id=event_id,
                        event_type=EventType.TOOL_RESULT
                    )
                    message_index += 1

            # 生成完成，保存助手消息
            generation_time = (datetime.utcnow() - start_time).total_seconds()

            # ✅ 如果有未保存的 thinking，保存到 timeline
            if thinking_buffer and not has_sent_thinking:
                timeline.insert(0, {  # 插入到最前面
                    "type": "thinking",
                    "content": thinking_buffer.strip(),
                    "timestamp": start_time.isoformat()
                })

            # ✅ 构建 structured_content，包含时间线
            structured_content = {
                "timeline": timeline  # 按时间顺序记录所有事件
            } if timeline else None

            assistant_message = self.create_message(
                session_id=session_id,
                role="assistant",
                content=assistant_content,
                message_type="text",
                model_name=target_model_id,
                generation_time=generation_time,
                structured_content=structured_content
            )

            # 发送done消息，使用数据库中的真实message_id
            event_id, current_event_type = self._get_next_event_id(
                EventType.MESSAGE_DONE, current_event_type, event_id
            )
            yield self._wrap_ws_message(
                event_data={
                    "message_id": str(assistant_message.id),  # 使用真实的数据库ID
                    "conversation_id": str(session_id),
                    "status": MessageStatus.COMPLETED,
                    "is_finish": True,
                    "message_index": message_index,
                    "generation_time": generation_time
                },
                event_id=event_id,
                event_type=EventType.MESSAGE_DONE
            )

            # 如果是第一条消息，异步生成标题
            if session.message_count == 2:  # 用户消息 + AI回复
                # TODO: 实现异步标题生成
                pass

        except Exception as e:
            LOGGER.exception("生成回复失败")
            yield self._wrap_ws_message(
                event_data={
                    "message_id": assistant_message_id,
                    "conversation_id": str(session_id),
                    "message": {
                        "id": str(uuid4()),
                        "content_type": ContentType.ERROR,
                        "content": json.dumps({"error": str(e)})
                    },
                    "status": MessageStatus.ERROR,
                    "is_finish": True,
                    "message_index": message_index
                },
                event_id=event_id,
                event_type=EventType.ERROR
            )

        # ✅ 不需要关闭 client，由 factory 统一管理连接池

    async def generate_title(self, session_id: UUID) -> Optional[str]:
        """异步生成会话标题

        Args:
            session_id: 会话ID

        Returns:
            生成的标题
        """
        # TODO: 实现标题生成逻辑
        return None

