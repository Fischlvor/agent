"""聊天服务层，处理会话和消息的业务逻辑"""

import json
import logging
import re
from datetime import datetime
from typing import AsyncIterator, Dict, List, Optional, Tuple, Any
from uuid import uuid4

from sqlalchemy import and_, desc, or_
from sqlalchemy.orm import Session

#from app.ai.agent_service import AgentService
from app.ai.adk_agent_adapter import AgentService  # ✅ 使用 ADK Agent 适配器
from app.ai.factory import FACTORY
from app.constants import EventType, ContentType, MessageStatus
from app.core.prompts import DEFAULT_SYSTEM_PROMPT
from app.core.redis_client import redis_service
from app.models.ai_model import AIModel
from app.models.chat import ChatMessage
from app.models.invocation import ToolInvocation
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
            and_(
                ChatSession.user_id == user.id,
                or_(ChatSession.status != 'deleted', ChatSession.status.is_(None))
            )
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

    def get_session(self, session_id: str, user: User) -> Optional[ChatSession]:
        """获取单个会话

        Args:
            session_id: 会话ID
            user: 用户对象

        Returns:
            会话对象，如果不存在或不属于该用户则返回None
        """
        return self.db.query(ChatSession).filter(
            and_(
                ChatSession.session_id == session_id,
                ChatSession.user_id == user.id,
                or_(ChatSession.status != 'deleted', ChatSession.status.is_(None))
            )
        ).first()

    def update_session(
        self,
        session_id: str,
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

    def delete_session(self, session_id: str, user: User) -> bool:
        """删除会话（软删除）

        Args:
            session_id: 会话ID
            user: 用户对象

        Returns:
            是否成功删除
        """
        session = self.get_session(session_id, user)
        if not session:
            return False

        # 软删除：设置状态为 deleted
        session.status = 'deleted'
        self.db.commit()
        return True

    # ============ 消息管理 ============

    def create_user_message(
        self,
        session_id: str,
        user: User,
        content: str,
        model_id: Optional[str] = None,
        parent_message_id: Optional[str] = None
    ) -> ChatMessage:
        """创建用户消息

        Args:
            session_id: 会话ID
            user: 用户对象
            content: 消息内容
            model_id: 模型ID
            parent_message_id: 父消息ID（用于编辑消息时的关联）

        Returns:
            创建的用户消息对象
        """
        session = self.get_session(session_id, user)
        if not session:
            raise ValueError("会话不存在")

        # 创建用户消息
        user_message = ChatMessage(
            message_id=str(uuid4()),
            session_id=session.session_id,
            parent_message_id=parent_message_id,
            role="user",
            content=content,
            message_type="text",
            status="completed",
            is_edited=bool(parent_message_id),  # 如果有父消息，标记为已编辑
            model_name=model_id or session.ai_model,
            sent_at=datetime.utcnow()
        )

        self.db.add(user_message)
        session.last_activity_at = datetime.utcnow()
        session.message_count += 1

        self.db.commit()
        self.db.refresh(user_message)

        return user_message

    def get_messages(
        self,
        session_id: str,
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
        session_id: str,
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
            ChatSession.session_id == session_id
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
        message_id: str,
        user: User,
        new_content: str  # pylint: disable=unused-argument
    ) -> bool:
        """编辑消息（软删除原消息及后续回复，不创建新消息）

        Args:
            message_id: 原消息ID
            user: 用户对象
            new_content: 新内容（保留用于API兼容性，实际由前端通过 sendMessage 重新发送）

        Returns:
            是否成功
        """
        original_message = self.db.query(ChatMessage).filter(
            ChatMessage.message_id == message_id
        ).first()

        if not original_message:
            return False

        # 检查权限
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.session_id == original_message.session_id,
                ChatSession.user_id == user.id
            )
        ).first()

        if not session:
            return False

        session_id = original_message.session_id

        # ✅ 统一处理逻辑（适用所有场景）

        # 1. 检查是否有摘要消息
        summary_message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_summary == True,
                ChatMessage.is_deleted == False
            )
        ).first()

        # 2. 如果被编辑的消息已被摘要，需要恢复上下文
        if original_message.is_summarized:
            LOGGER.info(f"📝 编辑已摘要的消息 {message_id}，恢复历史上下文")

            # 恢复该消息及之前所有被摘要的消息
            messages_to_restore = self.db.query(ChatMessage).filter(
                and_(
                    ChatMessage.session_id == session_id,
                    ChatMessage.is_summarized == True,
                    ChatMessage.created_at <= original_message.created_at
                )
            ).all()

            for msg in messages_to_restore:
                msg.is_summarized = False

            # 删除摘要消息
            if summary_message:
                summary_message.is_deleted = True
                LOGGER.info(f"🗑️ 删除摘要消息，恢复完整历史")

        # 3. 软删除原消息
        original_message.is_deleted = True

        # 4. 软删除该消息之后的所有消息（包括摘要消息之后的）
        later_messages = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.created_at > original_message.created_at,
                ChatMessage.is_deleted == False
            )
        ).all()

        for msg in later_messages:
            msg.is_deleted = True
            LOGGER.debug(f"🗑️ 软删除后续消息: {msg.id}")

        # 5. 更新会话统计和上下文token
        session.message_count = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False
            )
        ).count()
        session.current_context_tokens = self.calculate_current_context_tokens(session_id)
        session.last_activity_at = datetime.utcnow()
        self.db.commit()

        LOGGER.info(f"✅ 消息编辑完成: 已删除原消息和后续回复，等待前端发送新消息")

        return True

    def delete_message(self, message_id: str, user: User) -> bool:
        """删除消息（软删除）

        Args:
            message_id: 消息ID
            user: 用户对象

        Returns:
            是否成功删除
        """
        message = self.db.query(ChatMessage).filter(
            ChatMessage.message_id == message_id
        ).first()

        if not message:
            return False

        # 检查权限
        session = self.db.query(ChatSession).filter(
            and_(
                ChatSession.session_id == message.session_id,
                ChatSession.user_id == user.id
            )
        ).first()

        if not session:
            return False

        message.is_deleted = True
        self.db.commit()
        return True

    # ============ Token 计算 ============

    def enrich_session_with_context_info(
        self,
        session: ChatSession
    ) -> Dict:
        """为会话添加上下文使用信息

        Args:
            session: 会话对象

        Returns:
            包含上下文信息的字典
        """
        # 获取模型配置
        model_config = self.get_model_by_id(session.ai_model or "qwen3:8b")
        max_context = model_config.max_context_length if model_config else 32768

        # 计算使用百分比
        usage_percent = 0.0
        if max_context > 0 and session.current_context_tokens:
            usage_percent = round((session.current_context_tokens / max_context) * 100, 1)

        # 转换为字典并添加字段
        session_dict = {
            "id": session.id,
            "session_id": session.session_id,
            "user_id": session.user_id,
            "title": session.title,
            "description": session.description,
            "status": session.status,
            "is_pinned": session.is_pinned,
            "last_activity_at": session.last_activity_at,
            "message_count": session.message_count,
            "total_tokens": session.total_tokens,
            "current_context_tokens": session.current_context_tokens,
            "ai_model": session.ai_model,
            "temperature": session.temperature,
            "max_tokens": session.max_tokens,
            "system_prompt": session.system_prompt,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            # 新增字段
            "max_context_tokens": max_context,
            "context_usage_percent": usage_percent
        }

        return session_dict

    def calculate_current_context_tokens(
        self,
        session_id: str
    ) -> int:
        """计算当前上下文的token总数

        下一轮对话的上下文包括：
        1. 最新消息的 prompt_tokens（之前的所有上下文）
        2. 最新助手消息的 completion_tokens（这条回复也会成为下次的上下文）

        即：current_context_tokens = latest_message.total_tokens

        Args:
            session_id: 会话ID

        Returns:
            当前上下文token总数
        """
        # 获取最新一条未删除的助手消息
        latest_message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False,
                ChatMessage.role == "assistant"  # 只看助手消息，因为它有完整的token统计
            )
        ).order_by(ChatMessage.created_at.desc()).first()

        if not latest_message or not latest_message.total_tokens:
            return 0

        # 下次对话的上下文 = 当前消息的 total_tokens
        # (prompt_tokens + completion_tokens)
        current_context = latest_message.total_tokens

        LOGGER.debug(f"上下文Token: {current_context} (来自消息 {latest_message.message_id}: prompt={latest_message.prompt_tokens} + completion={latest_message.completion_tokens})")

        return current_context

    # ============ 摘要生成 ============

    async def generate_session_summary(
        self,
        session_id: str,
        user: User
    ) -> Optional[ChatMessage]:
        """生成会话摘要

        Args:
            session_id: 会话ID
            user: 用户对象

        Returns:
            摘要消息对象，如果不需要摘要则返回None
        """
        session = self.get_session(session_id, user)
        if not session:
            raise ValueError("会话不存在")

        # 获取所有未删除且未被摘要的消息
        all_messages = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False,
                ChatMessage.is_summarized == False,
                ChatMessage.is_summary == False
            )
        ).order_by(ChatMessage.created_at).all()

        # 如果消息少于6条，不需要摘要
        if len(all_messages) <= 5:
            LOGGER.info(f"会话 {session_id} 消息数不足，无需生成摘要")
            return None

        # 保留最近5条，其他的生成摘要
        messages_to_summarize = all_messages[:-5]
        messages_to_keep = all_messages[-5:]

        # 构建摘要提示词
        conversation_text = "\n\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages_to_summarize
        ])

        summary_prompt = f"""请对以下对话进行简洁的摘要，保留关键信息和上下文：

{conversation_text}

要求：
1. 概括主要讨论的话题和结论
2. 保留重要的事实信息
3. 控制在200字以内

摘要："""

        # 调用LLM生成摘要
        model_config = self.get_model_by_id(session.ai_model or "qwen3:8b")
        if not model_config:
            raise ValueError("模型不存在")

        client = FACTORY.create_client(
            provider=model_config.provider,
            model_name=model_config.model_name,
            api_base=model_config.api_base
        )

        try:
            # 非流式调用生成摘要
            response = await client.chat(
                messages=[{"role": "user", "content": summary_prompt}],
                stream=False
            )
            summary_content = response.get("content", "")

            # 创建摘要消息
            summary_message = ChatMessage(
                message_id=str(uuid4()),
                session_id=session_id,
                role="system",
                content=f"【对话摘要】{summary_content}",
                message_type="summary",
                is_summary=True,
                sent_at=datetime.utcnow(),
                status="sent",
                # Token统计（假设response中有，否则需要估算）
                prompt_tokens=len(summary_prompt.split()) * 2,  # 粗略估算
                completion_tokens=len(summary_content.split()) * 2,
                total_tokens=len(summary_prompt.split()) * 2 + len(summary_content.split()) * 2
            )

            self.db.add(summary_message)

            # 标记旧消息为已摘要
            for msg in messages_to_summarize:
                msg.is_summarized = True

            self.db.commit()
            self.db.refresh(summary_message)

            LOGGER.info(f"✅ 会话 {session_id} 摘要已生成，覆盖 {len(messages_to_summarize)} 条消息")

            # 同时保存到Redis缓存（2小时）
            redis_service.save_session_summary(str(session_id), summary_content, expire_seconds=7200)

            return summary_message

        except Exception as e:
            LOGGER.error(f"生成摘要失败: {e}")
            return None
        # 注意：不要关闭客户端，因为是从 FACTORY 缓存获取的共享实例

    # ============ AI对话 ============

    async def send_message_streaming(
        self,
        session_id: str,
        user: User,
        content: str,
        model_id: Optional[str] = None,
        skip_user_message: bool = False,
        edited_message_id: Optional[str] = None
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

        # ✅ 先创建一个pending状态的assistant消息占位符（用于外键约束）
        assistant_message_placeholder = ChatMessage(
            message_id=str(uuid4()),
            session_id=session_id,
            role="assistant",
            content="",  # 空内容，稍后更新
            message_type="text",
            status="pending",  # 标记为pending
            model_name=target_model_id,
            sent_at=datetime.utcnow()
        )
        self.db.add(assistant_message_placeholder)
        self.db.flush()  # 立即写入以获取ID，但不提交
        assistant_message_id = assistant_message_placeholder.message_id

        # ✅ 增加消息计数（创建助手消息）
        session.message_count += 1

        # 发送开始消息
        event_id, current_event_type = self._get_next_event_id(
            EventType.MESSAGE_START, current_event_type, event_id
        )
        yield self._wrap_ws_message(
            event_data={
                "message_id": str(assistant_message_id),
                "conversation_id": str(session_id),
                "status": MessageStatus.PENDING,
                "message_index": message_index
            },
            event_id=event_id,
            event_type=EventType.MESSAGE_START
        )
        message_index += 1

        # ✅ 步骤1：检查是否需要生成摘要（在获取历史前）
        model_max_context = model_config.max_context_length or 32768
        should_generate_summary = False

        if session.current_context_tokens >= int(model_max_context * 0.9):
            LOGGER.info(f"🔄 会话 {session_id} 上下文达到阈值 ({session.current_context_tokens}/{model_max_context}), 触发摘要生成")
            summary_message = await self.generate_session_summary(session_id, user)
            should_generate_summary = True

        # ✅ 步骤2：获取有效消息（未删除且未被摘要的）
        # ⚠️ 排除刚创建的 pending 状态的助手占位符消息
        effective_messages = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False,
                ChatMessage.is_summarized == False,  # 不包含已被摘要的
                ChatMessage.message_id != assistant_message_id  # ⚠️ 排除占位符
            )
        ).order_by(ChatMessage.created_at).all()

        # ✅ 步骤3：获取摘要消息（如果有）
        summary_message = self.db.query(ChatMessage).filter(
            and_(
                ChatMessage.session_id == session_id,
                ChatMessage.is_summary == True,
                ChatMessage.is_deleted == False
            )
        ).order_by(ChatMessage.created_at.desc()).first()

        # ✅ 步骤4：构建上下文消息列表（摘要 + 有效消息）
        messages = []

        # 添加摘要（如果有）
        if summary_message:
            messages.append({"role": "system", "content": summary_message.content})
            LOGGER.info(f"✅ 包含摘要消息: {summary_message.content[:50]}...")

        # ✅ 根据是否跳过用户消息来决定如何处理历史
        if skip_user_message:
            # 编辑重新生成：使用全部有效消息
            for msg in effective_messages:
                messages.append({"role": msg.role, "content": msg.content})
        else:
            # 正常发送：排除最后一条（刚创建的用户消息），然后添加当前内容
            for msg in effective_messages[:-1]:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": content})

        # 创建AI客户端
        client = FACTORY.create_client(
            provider=model_config.provider,
            model_name=model_config.model_id,
            base_url=model_config.base_url
        )

        # 创建Agent服务
        agent = AgentService(client, debug=False)

        # ✅ 设置LLM适配器的追踪信息
        if hasattr(agent, 'adk_llm') and agent.adk_llm:
            object.__setattr__(agent.adk_llm, 'db_session', self.db)
            object.__setattr__(agent.adk_llm, 'current_session_id', session_id)
            object.__setattr__(agent.adk_llm, 'current_message_id', assistant_message_id)  # 这是UUID对象
            object.__setattr__(agent.adk_llm, 'llm_sequence_counter', 0)

        # 流式生成
        assistant_content = ""
        has_sent_thinking = False  # ✅ 是否已发送 thinking
        thinking_buffer = ""  # ✅ 累积的 thinking 内容
        last_sent_content_len = 0  # ✅ 记录已发送的 content 长度（用于多轮思考）
        current_thinking_id = None  # ✅ 当前正在进行的 thinking 块的 ID
        timeline = []  # ✅ 记录事件时间线（thinking、tool_call、content）
        start_time = datetime.utcnow()

        # ✅ 工具调用追踪
        tool_sequence_counter = 0  # 工具调用序号
        tool_invocation_records = {}  # {tool_call_id: ToolInvocation对象}
        tool_start_times = {}  # {tool_call_id: start_time}

        # ✅ Token 统计信息
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0

        # ✅ 从缓存获取用户系统提示词（优先级：缓存 > 会话设置 > 默认值）
        cached_system_prompt = redis_service.get_user_preference(str(user.id), "system_prompt")
        if cached_system_prompt:
            system_prompt = cached_system_prompt
        else:
            system_prompt = session.system_prompt or DEFAULT_SYSTEM_PROMPT
            # 保存到缓存（24小时）
            redis_service.save_user_preference(str(user.id), "system_prompt", system_prompt, expire_seconds=86400)

        try:
            async for chunk in agent.run_streaming(
                messages=messages,
                system_prompt=system_prompt,
                tools=None,  # ✅ 工具通过 ADK 自动加载（adk_agent_adapter.py）
                user_id=str(user.id),  # ✅ 传递真实的用户ID
                session_id=str(session_id)  # ✅ 传递真实的会话ID
            ):
                if chunk["type"] == "content":
                    content_delta = chunk["content"]
                    assistant_content += content_delta

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
                                        "message_id": str(assistant_message_id),
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
                                        "message_id": str(assistant_message_id),
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
                        "message_id": str(assistant_message_id),
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
                        "message_id": str(assistant_message_id),
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
                                        "message_id": str(assistant_message_id),
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
                        tool_name = tool_call["function"]["name"]
                        tool_args = tool_call["function"]["arguments"]
                        tool_sequence_counter += 1
                        tool_start_times[tool_call_id] = datetime.utcnow()

                        # ✅ 创建工具调用记录（pending状态）
                        try:
                            # 获取最近保存的 LLM 序号（从 LLM 适配器传递过来）
                            current_llm_sequence = None
                            if hasattr(agent, 'adk_llm') and hasattr(agent.adk_llm, 'last_llm_sequence'):
                                current_llm_sequence = agent.adk_llm.last_llm_sequence

                            tool_invocation = ToolInvocation(
                                message_id=assistant_message_id,
                                session_id=session_id,
                                sequence_number=tool_sequence_counter,
                                triggered_by_llm_sequence=current_llm_sequence,
                                tool_name=tool_name,
                                arguments=tool_args,
                                result=None,
                                status="pending",
                                cache_hit=False,
                                error_message=None,
                                duration_ms=None,
                                created_at=datetime.utcnow()
                            )
                            self.db.add(tool_invocation)
                            self.db.flush()  # 获取ID但不提交
                            tool_invocation_records[tool_call_id] = tool_invocation

                            LOGGER.info(f"✅ 创建工具调用记录 #{tool_sequence_counter}: {tool_name}")
                        except Exception as e:
                            LOGGER.error(f"创建工具调用记录失败: {e}", exc_info=True)

                        # ✅ 添加到时间线
                        timeline.append({
                            "type": "tool_call",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "tool_id": tool_call_id,
                            "status": "pending",
                            "timestamp": datetime.utcnow().isoformat()
                        })
                        event_id, current_event_type = self._get_next_event_id(
                            EventType.TOOL_CALL, current_event_type, event_id
                        )
                        yield self._wrap_ws_message(
                            event_data={
                        "message_id": str(assistant_message_id),
                        "conversation_id": str(session_id),
                                "message": {
                                    "id": tool_call_id,
                                    "content_type": ContentType.TOOL_CALL,
                                    "content": json.dumps({
                                        "name": tool_name,
                                        "args": tool_args
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

                            # ✅ 更新数据库记录
                            if tool_result_id and tool_result_id in tool_invocation_records:
                                try:
                                    invocation = tool_invocation_records[tool_result_id]
                                    start_time_key = tool_result_id

                                    # 计算耗时
                                    duration_ms = None
                                    if start_time_key in tool_start_times:
                                        duration = (datetime.utcnow() - tool_start_times[start_time_key]).total_seconds()
                                        duration_ms = int(duration * 1000)

                                    # 更新记录
                                    invocation.result = str(chunk["result"]) if chunk["result"] else None
                                    invocation.status = "success"
                                    invocation.duration_ms = duration_ms

                                    # 检查是否命中缓存（从result中判断）
                                    # TODO: 如果MCP返回缓存标志，在这里更新

                                    self.db.flush()

                                    LOGGER.info(
                                        f"✅ 更新工具调用记录: {invocation.tool_name} "
                                        f"status=success, duration={duration_ms}ms"
                                    )
                                except Exception as e:
                                    LOGGER.error(f"更新工具调用记录失败: {e}", exc_info=True)

                            break

                    event_id, current_event_type = self._get_next_event_id(
                        EventType.TOOL_RESULT, current_event_type, event_id
                    )
                    yield self._wrap_ws_message(
                        event_data={
                            "message_id": str(assistant_message_id),
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

                elif chunk["type"] == "llm_invocation":
                    # ✅ LLM调用完成事件
                    invocation_data = chunk.get("invocation_data", {})

                    # 计算会话累积token (实时累加)
                    current_call_tokens = invocation_data.get('total_tokens', 0)
                    session.total_tokens = (session.total_tokens or 0) + current_call_tokens

                    # 计算上下文使用百分比
                    context_usage_percent = 0.0
                    if model_max_context > 0:
                        context_usage_percent = round((session.total_tokens / model_max_context) * 100, 2)

                    # 推送LLM调用完成事件
                    event_id, current_event_type = self._get_next_event_id(
                        EventType.LLM_INVOCATION_COMPLETE, current_event_type, event_id
                    )
                    yield self._wrap_ws_message(
                        event_data={
                            "message_id": str(assistant_message_id),
                            "conversation_id": str(session_id),
                            "invocation": {
                                "sequence": invocation_data.get('sequence'),
                                "tokens": {
                                    "prompt": invocation_data.get('prompt_tokens'),
                                    "completion": invocation_data.get('completion_tokens'),
                                    "total": invocation_data.get('total_tokens')
                                },
                                "duration_ms": invocation_data.get('duration_ms'),
                                "finish_reason": invocation_data.get('finish_reason')
                            },
                            "session_cumulative_tokens": session.total_tokens,
                            "context_usage_percent": context_usage_percent,
                            "message_index": message_index
                        },
                        event_id=event_id,
                        event_type=EventType.LLM_INVOCATION_COMPLETE
                    )
                    message_index += 1

                elif chunk["type"] == "usage":
                    # ✅ Token 统计信息（最终汇总，保留用于兼容）
                    usage = chunk.get("usage", {})
                    prompt_tokens = usage.get("prompt_tokens", 0)
                    completion_tokens = usage.get("completion_tokens", 0)
                    total_tokens = usage.get("total_tokens", 0)

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

            # ✅ 更新占位符消息（而不是创建新消息）
            assistant_message_placeholder.content = assistant_content
            assistant_message_placeholder.status = "completed"
            assistant_message_placeholder.generation_time = generation_time
            assistant_message_placeholder.structured_content = structured_content
            assistant_message_placeholder.prompt_tokens = prompt_tokens
            assistant_message_placeholder.completion_tokens = completion_tokens
            assistant_message_placeholder.total_tokens = total_tokens

            assistant_message = assistant_message_placeholder

            # ✅ 更新会话的 current_context_tokens 和 total_tokens
            session.current_context_tokens = self.calculate_current_context_tokens(session_id)
            # session.total_tokens 已经在每次LLM调用时累加了，这里不需要重复设置

            # ✅ 一次性提交所有更改（消息、invocations、session）
            self.db.commit()

            LOGGER.info(f"✅ 会话统计更新: current_context={session.current_context_tokens}/{model_max_context} tokens ({session.current_context_tokens/model_max_context*100:.1f}%), total_tokens={session.total_tokens}")

            # ✅ 清除会话摘要缓存（会话内容已更新）
            redis_service.delete_session_summary(str(session_id))

            # 发送done消息，使用数据库中的真实message_id
            event_id, current_event_type = self._get_next_event_id(
                EventType.MESSAGE_DONE, current_event_type, event_id
            )
            yield self._wrap_ws_message(
                event_data={
                    "message_id": assistant_message.message_id,  # 使用业务ID
                    "conversation_id": str(session_id),
                    "status": MessageStatus.COMPLETED,
                    "is_finish": True,
                    "message_index": message_index,
                    "generation_time": generation_time,
                    # ✅ 推送上下文信息，前端直接使用，无需额外请求
                    "context_info": {
                        "current_context_tokens": session.current_context_tokens,
                        "max_context_tokens": model_max_context
                    },
                    # ✅ 推送会话统计信息，用于更新会话列表显示
                    "session_info": {
                        "session_id": str(session_id),
                        "message_count": session.message_count,  # ✅ 总消息数（包括用户和助手）
                        "total_prompt_tokens": prompt_tokens,  # ✅ 当前对话的 prompt tokens
                        "total_completion_tokens": completion_tokens,  # ✅ 当前对话的 completion tokens
                        "total_tokens": session.total_tokens,  # ✅ 会话累计 tokens
                        "last_activity_at": session.last_activity_at.isoformat() if session.last_activity_at else None
                    }
                },
                event_id=event_id,
                event_type=EventType.MESSAGE_DONE
            )

            # 如果是第一条消息，异步生成标题
            if session.message_count == 2:  # 用户消息 + AI回复
                # ✅ 异步生成会话标题（不阻塞响应）并推送给前端
                import asyncio
                asyncio.create_task(self.generate_title(session_id, str(user.id)))

        except Exception as e:
            LOGGER.exception("生成回复失败")
            yield self._wrap_ws_message(
                event_data={
                        "message_id": str(assistant_message_id),
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

    async def generate_title(self, session_id: str, user_id: Optional[str] = None) -> Optional[str]:
        """异步生成会话标题（使用 LLM 总结）并推送给前端

        Args:
            session_id: 会话ID
            user_id: 用户ID（用于WebSocket推送）

        Returns:
            生成的标题
        """
        try:
            # ✅ 获取会话信息
            session = self.db.query(ChatSession).filter(
                ChatSession.session_id == session_id
            ).first()

            if not session:
                return None

            # ✅ 严格判断：只在第一轮对话（2条消息）时生成标题
            # 这样即使用户修改了标题，也不会在后续对话中重复生成
            if session.message_count != 2:
                LOGGER.debug(f"会话 {session_id} 消息数为 {session.message_count}，跳过标题生成")
                return None

            # ✅ 获取前2条消息
            messages = self.db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False
            ).order_by(ChatMessage.sent_at.asc()).limit(2).all()

            if len(messages) < 2:
                LOGGER.warning(f"会话 {session_id} 消息数不足，无法生成标题")
                return None

            user_message = messages[0].content
            assistant_message = messages[1].content

            # ✅ 使用 LLM 生成标题（智能总结）
            title = await self._generate_title_with_llm(user_message, assistant_message, session)

            # ✅ 更新会话标题
            if title:
                old_title = session.title
                session.title = title
                self.db.commit()
                LOGGER.info(f"✅ 会话 {session_id} 标题已生成: '{old_title}' → '{title}'")

                # ✅ 通过 WebSocket 推送标题更新给前端
                if user_id:
                    await self._push_title_update(user_id, session_id, title)
            else:
                LOGGER.warning(f"⚠️  会话 {session_id} 标题生成为空，保持原标题")

            return title

        except Exception as e:
            LOGGER.error(f"❌ 生成会话标题失败: {e}")
            self.db.rollback()
            return None

    async def _push_title_update(self, user_id: str, session_id: str, title: str):
        """通过 WebSocket 推送标题更新

        Args:
            user_id: 用户ID
            session_id: 会话ID
            title: 新标题
        """
        try:
            # 导入 WebSocket manager
            from app.api.endpoints.chat_ws import manager
            from app.constants import EventType

            # 构建标题更新事件（使用 conversation_id 以保持与其他事件一致）
            event_data = {
                "conversation_id": session_id,  # ✅ 使用 conversation_id 保持一致
                "title": title,
                "updated_at": datetime.utcnow().isoformat()
            }

            # 推送给前端
            await manager.send_message(user_id, {
                "event_data": json.dumps(event_data, ensure_ascii=False),
                "event_id": "0",
                "event_type": EventType.SESSION_TITLE_UPDATED
            })

            LOGGER.info(f"✅ 已推送标题更新到用户 {user_id}: {title}")

        except Exception as e:
            # WebSocket 推送失败不应该影响标题生成
            LOGGER.warning(f"⚠️  推送标题更新失败: {e}")

    async def _generate_title_with_llm(
        self,
        user_message: str,
        assistant_message: str,
        session: ChatSession
    ) -> str:
        """使用 LLM 生成会话标题

        Args:
            user_message: 用户消息
            assistant_message: 助手回复
            session: 会话对象

        Returns:
            生成的标题
        """
        # 构建标题生成提示词
        title_prompt = f"""请根据以下对话内容，生成一个简洁明了的标题（8-15字以内，不要使用标点符号）。

用户问题：{user_message}
AI回复：{assistant_message}...

要求：
1. 提取对话的核心主题
2. 使用简洁的短语或问句形式
3. 8-15个字以内
4. 不要加引号或其他标点
5. 直接返回标题文本，不要其他内容

标题："""

        # 获取模型配置
        model_config = self.get_model_by_id(session.ai_model or "qwen3:8b")
        if not model_config:
            # 降级：如果模型不可用，返回通用标题
            LOGGER.warning(f"模型配置不存在，使用默认标题")
            return "对话记录"

        # 创建 LLM 客户端
        client = FACTORY.create_client(
            provider=model_config.provider,
            model_name=model_config.model_id,
            base_url=model_config.base_url
        )

        try:
            # 非流式调用生成标题
            response = await client.chat(
                messages=[{"role": "user", "content": title_prompt}],
                stream=False
            )

            # 提取标题内容
            title = response.get("content", "").strip()

            # 移除思考标签（如果LLM返回了）
            if '<think>' in title:
                title = title.split('</think>')[-1].strip()

            # 清理可能的引号、标点等（首尾）
            title = title.strip('"\'「」《》『』【】""''。，！？、;：')

            # 如果LLM返回了多行，只取第一行
            if '\n' in title:
                title = title.split('\n')[0].strip()

            # 移除可能的"标题："前缀
            if title.startswith('标题：') or title.startswith('标题:'):
                title = title[3:].strip()

            # 如果标题为空或太短，使用通用标题
            if not title or len(title) < 2:
                LOGGER.warning(f"LLM 返回的标题为空或太短: '{title}'，使用通用标题")
                return "对话记录"

            # 如果标题过长（超过30字），说明LLM没有遵守指令，重新生成
            if len(title) > 30:
                LOGGER.warning(f"LLM 生成的标题过长({len(title)}字): '{title}'，使用通用标题")
                return "对话记录"

            LOGGER.info(f"✅ LLM 生成标题: {title}")
            return title

        except Exception as e:
            LOGGER.error(f"❌ LLM 生成标题失败: {e}")
            # 降级：返回通用标题，而不是截取用户消息
            return "对话记录"
        # 注意：不要关闭客户端，因为是从 FACTORY 缓存获取的共享实例


