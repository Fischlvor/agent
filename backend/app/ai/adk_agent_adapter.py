"""
ADK Agent 适配器

将 ADK Agent 适配到我们现有的接口，保持与 AgentService 的兼容性
"""

from typing import List, Dict, Any, AsyncIterator, Optional
import uuid
import logging
from google.adk import Agent, Runner
from google.adk.tools import FunctionTool
from google.genai.types import Content, Part

from app.ai.adk_llm_adapter import ADKLlmAdapter
from app.ai.adk_session_service import create_simple_session_service
from app.ai.frontend_event_adapter import create_frontend_event_adapter  # ✅ 前端展示格式转换
from app.ai.mcp_tools_adapter import setup_mcp_tools_for_session, create_mcp_tools_for_adk  # ✅ 真正的 MCP 工具
from app.ai.clients.base import BaseAIClient

LOGGER = logging.getLogger(__name__)

# ============ 全局缓存（跨实例共享）============
# 避免每次创建新的 ADKAgentAdapter 实例时都重新初始化工具
_GLOBAL_MCP_CLIENT_CACHE: Dict[str, Any] = {}
_GLOBAL_ADK_TOOLS_CACHE: Dict[str, List] = {}
_GLOBAL_AGENT_CACHE: Dict[str, Any] = {}  # Agent 实例缓存
_GLOBAL_RUNNER_CACHE: Dict[str, Any] = {}  # Runner 实例缓存


class ADKAgentAdapter:
    """
    ADK Agent 适配器

    目标：保持与原 AgentService 完全相同的接口，内部使用 ADK Agent
    """

    def __init__(
        self,
        client: BaseAIClient,
        max_iterations: int = 50,
        debug: bool = False
    ):
        """
        初始化 Agent 适配器

        Args:
            client: 我们的 LLM 客户端
            max_iterations: 最大迭代次数
            debug: 是否启用调试模式
        """
        self.our_client = client
        self.max_iterations = max_iterations
        self.debug = debug

        # 创建 ADK LLM 适配器
        self.adk_llm = ADKLlmAdapter(our_client=client, model_name="custom")
        # ✅ 保存自己的引用，方便 LLM adapter 访问历史消息
        self.adk_llm.agent_adapter = self

        # 创建会话服务
        self.session_service = create_simple_session_service()

        # ✅ 创建前端事件适配器（ADK 事件 → 前端展示格式）
        self.event_adapter = create_frontend_event_adapter(debug=debug)

        # ADK Agent 和 Runner 实例（延迟创建，在 run 时创建）
        self.adk_agent: Optional[Agent] = None
        self.adk_runner: Optional[Runner] = None

    async def run_streaming(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        流式运行 Agent（保持原接口）

        Args:
            messages: 对话历史
            system_prompt: 系统提示词（作为第一条消息传递给 LLM）
            tools: 工具列表（OpenAI 格式的 schema）
            user_id: 用户ID（用于区分不同用户的会话）
            session_id: 会话ID（用于保持历史上下文）

        Yields:
            字典格式的 chunk:
            - {"type": "content", "content": "..."}
            - {"type": "tool_call", "name": "...", "args": {...}}
            - {"type": "tool_result", "name": "...", "result": "..."}
        """
        # 如果提供了 system_prompt，且第一条消息不是 system，则插入到开头
        if system_prompt and (not messages or messages[0].get("role") != "system"):
            messages = [{"role": "system", "content": system_prompt}] + messages

        # ============ 步骤 1：获取或创建 ADK Agent 和 Runner（带全局缓存）============
        cache_key = f"{session_id or 'default'}:{self.adk_llm.model_name}"  # 包含模型名，不同模型使用不同缓存

        # ✅ 使用全局缓存，避免每次创建新实例都重新初始化
        if cache_key not in _GLOBAL_RUNNER_CACHE:
            LOGGER.info(f"为会话 {cache_key} 初始化 Agent 和工具（首次创建）")

            # 创建 MCP client 和工具
            mcp_client = await setup_mcp_tools_for_session(session_id or "default")
            adk_tools = await create_mcp_tools_for_adk(mcp_client)

            # 缓存
            _GLOBAL_MCP_CLIENT_CACHE[cache_key] = mcp_client
            _GLOBAL_ADK_TOOLS_CACHE[cache_key] = adk_tools

            # 创建 ADK Agent
            agent = Agent(
                name="chat_agent",
                model=self.adk_llm,
                tools=adk_tools,
            )
            _GLOBAL_AGENT_CACHE[cache_key] = agent

            # 创建 Runner
            runner = Runner(
                app_name="chat_app",
                agent=agent,
                session_service=self.session_service
            )
            _GLOBAL_RUNNER_CACHE[cache_key] = runner
        else:
            LOGGER.debug(f"使用缓存的 Agent 和工具（会话 {cache_key}）")

        # 使用缓存的实例
        self.adk_agent = _GLOBAL_AGENT_CACHE[cache_key]
        self.adk_runner = _GLOBAL_RUNNER_CACHE[cache_key]

        # ✅ 更新 adk_llm 的引用（确保能访问最新的 _history_messages）
        self.adk_llm.agent_adapter = self

        # ============ 步骤 2：准备 Runner 参数 ============
        adk_user_id = user_id or "default_user"
        adk_session_id = session_id or str(uuid.uuid4())

        # 保存历史消息（除最后一条），供 LLM adapter 使用
        self._history_messages = messages[:-1] if len(messages) > 1 else []

        # 将最后一条消息转换为 Content 对象（作为新消息）
        last_message = messages[-1] if messages else {"role": "user", "content": ""}
        new_message = Content(
            role=last_message.get("role", "user"),
            parts=[Part(text=last_message.get("content", ""))]
        )

        # ============ 步骤 3：运行 ADK Runner（流式） ============
        try:
            async for event in self._run_adk_runner_streaming(
                user_id=adk_user_id,
                session_id=adk_session_id,
                new_message=new_message
            ):
                yield event

        except (RuntimeError, ValueError, ConnectionError) as e:
            LOGGER.error(f"ADK Agent 运行错误: {str(e)}", exc_info=True)
            # 返回错误
            yield {
                "type": "error",
                "error": str(e)
            }

    async def _run_adk_runner_streaming(
        self,
        user_id: str,
        session_id: str,
        new_message: Content
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        运行 ADK Runner 并转换为流式输出

        ✅ 简化版：
        - Ollama 返回的本身就是增量（已测试验证）
        - ADK LLM 适配器累积后再发送（保证完整性）
        - MCP 转换器直接提取即可
        - 不需要二次计算增量

        Args:
            user_id: 用户ID
            session_id: 会话ID
            new_message: 新消息（ADK Content 格式）

        Yields:
            我们格式的事件字典
        """
        try:
            # 运行 Runner（流式）
            async for event in self.adk_runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=new_message
            ):
                # ✅ 检查是否有pending的invocation数据需要发送
                if hasattr(self.adk_llm, 'pending_invocation_data') and self.adk_llm.pending_invocation_data:
                    invocation_data = self.adk_llm.pending_invocation_data
                    object.__setattr__(self.adk_llm, 'pending_invocation_data', None)  # 清除

                    yield {
                        "type": "llm_invocation",
                        "invocation_data": invocation_data
                    }

                # ✅ 使用前端事件适配器（ADK → 前端格式）
                async for frontend_event in self.event_adapter.convert_adk_event_stream(event):
                    # 转换为 ChatService 期望的格式
                    our_format = self._frontend_to_chat_format(frontend_event)
                    if our_format:
                        yield our_format

        except (RuntimeError, ValueError, ConnectionError) as e:
            raise e

    @staticmethod
    def clear_cache(session_id: Optional[str] = None, model_name: Optional[str] = None):
        """清理全局缓存

        Args:
            session_id: 如果指定，只清理该会话的缓存；否则清理所有缓存
            model_name: 如果指定，只清理特定模型的缓存
        """
        if session_id and model_name:
            # 清理指定会话和模型
            cache_key = f"{session_id}:{model_name}"
            _GLOBAL_MCP_CLIENT_CACHE.pop(cache_key, None)
            _GLOBAL_ADK_TOOLS_CACHE.pop(cache_key, None)
            _GLOBAL_AGENT_CACHE.pop(cache_key, None)
            _GLOBAL_RUNNER_CACHE.pop(cache_key, None)
            LOGGER.info(f"已清理会话 {cache_key} 的缓存")
        elif session_id:
            # 清理指定会话的所有模型
            keys_to_remove = [k for k in _GLOBAL_RUNNER_CACHE.keys() if k.startswith(f"{session_id}:")]
            for key in keys_to_remove:
                _GLOBAL_MCP_CLIENT_CACHE.pop(key, None)
                _GLOBAL_ADK_TOOLS_CACHE.pop(key, None)
                _GLOBAL_AGENT_CACHE.pop(key, None)
                _GLOBAL_RUNNER_CACHE.pop(key, None)
            LOGGER.info(f"已清理会话 {session_id} 的所有缓存")
        else:
            # 清理所有缓存
            _GLOBAL_MCP_CLIENT_CACHE.clear()
            _GLOBAL_ADK_TOOLS_CACHE.clear()
            _GLOBAL_AGENT_CACHE.clear()
            _GLOBAL_RUNNER_CACHE.clear()
            LOGGER.info("已清理所有会话的缓存")

    def _frontend_to_chat_format(self, frontend_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        转换前端事件为 ChatService 格式（最后一层适配）

        架构层次：
        1. ADK Event（Google ADK 格式）
        2. → 前端事件（标准化展示格式）
        3. → ChatService 格式（兼容现有接口）
        """
        event_type = frontend_event.get("type")

        if event_type == "content":
            return {
                "type": "content",
                "content": frontend_event.get("delta", "")
            }
        elif event_type == "thinking":
            # 思考内容也转为 content 类型（保持兼容）
            return {
                "type": "content",
                "content": frontend_event.get("delta", "")
            }
        elif event_type == "tool_call":
            # ✅ 转换为 ChatService 期望的格式（复数 tool_calls）
            tool_call = frontend_event.get("tool_call", {})
            return {
                "type": "tool_calls",  # ← 复数！
                "tool_calls": [{
                    "function": {
                        "name": tool_call.get("name"),
                        "arguments": tool_call.get("arguments", {})
                    }
                }]
            }
        elif event_type == "tool_result":
            # ✅ 提取工具名称（从 tool_result）
            tool_result = frontend_event.get("tool_result", {})
            return {
                "type": "tool_result",
                "tool_name": tool_result.get("name", ""),  # 需要工具名称来匹配
                "result": tool_result.get("result")
            }
        elif event_type == "llm_invocation":
            # ✅ LLM调用完成事件（每次LLM调用的详细统计）
            return {
                "type": "llm_invocation",
                "invocation_data": frontend_event.get("invocation_data", {})
            }
        elif event_type == "usage":
            # ✅ Token 统计信息
            return {
                "type": "usage",
                "usage": frontend_event.get("usage", {})
            }
        elif event_type == "error":
            return {
                "type": "error",
                "error": frontend_event.get("error")
            }

        return None



# ============ 向后兼容的别名 ============
# 可以用 AgentService 的名字导入，方便替换
AgentService = ADKAgentAdapter


# ============ 工厂函数 ============
def create_adk_agent(
    client: BaseAIClient,
    max_iterations: int = 50,
    debug: bool = False
) -> ADKAgentAdapter:
    """
    工厂函数：创建 ADK Agent 适配器

    Args:
        client: LLM 客户端
        max_iterations: 最大迭代次数
        debug: 调试模式

    Example:
        >>> from app.ai.factory import FACTORY
        >>> from app.ai.adk_agent_adapter import create_adk_agent
        >>>
        >>> client = FACTORY.create_client("ollama", "qwen3:8b")
        >>> agent = create_adk_agent(client)  # 默认使用真 MCP
        >>>
        >>> async for chunk in agent.run_streaming(messages, system_prompt, tools):
        >>>     print(chunk)
    """
    return ADKAgentAdapter(
        client=client,
        max_iterations=max_iterations,
        debug=debug
    )

