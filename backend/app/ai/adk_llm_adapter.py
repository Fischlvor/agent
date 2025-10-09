"""
ADK LLM 适配器

将我们的 LLM 客户端（QwenClient, OpenAIClient 等）适配到 ADK 的 BaseLlm 接口
"""

import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, List, Optional
from google.adk.models import BaseLlm
from google.adk.models import LlmRequest, LlmResponse
from google.genai.types import Content, Part, FunctionCall, GenerateContentResponseUsageMetadata
from app.ai.clients.base import BaseAIClient

LOGGER = logging.getLogger(__name__)


class ADKLlmAdapter(BaseLlm):
    """
    ADK LLM 适配器

    将我们的 BaseAIClient 适配到 ADK 的 BaseLlm 接口
    """

    # Pydantic 配置：允许额外字段和任意类型
    model_config = {"arbitrary_types_allowed": True, "extra": "allow"}

    def __init__(self, our_client: BaseAIClient, model_name: str = "custom", **kwargs):
        """
        初始化适配器

        Args:
            our_client: 我们的 LLM 客户端（QwenClient, OpenAIClient 等）
            model_name: 模型名称（用于标识）
        """
        # 调用父类初始化
        super().__init__(model=model_name, **kwargs)

        # 通过 __dict__ 直接设置字段，绕过 Pydantic 验证
        object.__setattr__(self, 'our_client', our_client)
        object.__setattr__(self, 'model_name', model_name)

    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = True,  # ✅ 默认启用流式
        **kwargs  # ✅ 接受其他可能的参数
    ) -> AsyncGenerator[LlmResponse, None]:
        """
        生成内容（ADK 要求的接口）

        ✅ 真正的流式传输：
        1. 调用 chat_stream 获取增量响应
        2. 累积内容并逐步返回
        3. 每次 yield 一个 LlmResponse（包含到目前为止的所有内容）
        """
        # ============ 步骤 1：转换请求格式 ============
        our_messages = self._convert_request_to_our_format(llm_request)

        # 添加历史消息（从 agent_adapter 传来的完整历史）
        if hasattr(self, 'agent_adapter') and hasattr(self.agent_adapter, '_history_messages'):
            history = self.agent_adapter._history_messages
            if history:
                our_messages = history + our_messages

        # 提取工具定义
        our_tools = self._extract_tools_from_request(llm_request)

        # ============ 步骤 2：调用流式客户端 ============
        accumulated_content = ""
        usage_metadata = None  # 用于保存 token 统计信息

        response = await self.our_client.chat(
            messages=our_messages,
            system_prompt=None,
            tools=our_tools,
            stream=True,
            **kwargs
        )

        # 处理流式响应
        has_tool_call = False
        llm_start_time = datetime.utcnow()  # 记录LLM调用开始时间
        collected_tool_calls = None  # 收集 tool_calls，在流结束后处理

        async for chunk in response:
            # ✅ 提取 token 统计信息（最后一个 chunk 包含）
            if chunk.get("done") and ("prompt_eval_count" in chunk or "eval_count" in chunk):
                prompt_count = chunk.get("prompt_eval_count", 0)
                completion_count = chunk.get("eval_count", 0)
                LOGGER.info(f"🔍 Ollama原始Token统计 - prompt_eval_count: {prompt_count}, eval_count: {completion_count}, prompt_cache_hit: {chunk.get('prompt_eval_duration', 0) == 0}")
                usage_metadata = GenerateContentResponseUsageMetadata(
                    prompt_token_count=prompt_count,
                    candidates_token_count=completion_count,
                    total_token_count=(prompt_count + completion_count)
                )

                # ✅ 保存 ModelInvocation 记录到数据库，并获取序号
                llm_sequence = self._save_model_invocation(
                    prompt_tokens=prompt_count,
                    completion_tokens=completion_count,
                    total_tokens=prompt_count + completion_count,
                    start_time=llm_start_time,
                    finish_reason="STOP"
                )
                # 保存最近的 LLM 序号，供工具调用使用
                if llm_sequence is not None:
                    object.__setattr__(self, 'last_llm_sequence', llm_sequence)

            # ✅ Ollama 流式响应格式：{"message": {"role": "assistant", "content": "..."}, "done": false}
            if "message" in chunk:
                message = chunk["message"]

                # 提取增量内容
                if "content" in message and message["content"]:
                    delta = message["content"]
                    accumulated_content += delta  # 保留累积用于工具调用场景

                    # ✅ 返回增量内容（delta），不是累积内容！
                    adk_response = self._create_streaming_response(delta)
                    yield adk_response

                # ✅ 收集工具调用（不立即yield，等done时再处理）
                if "tool_calls" in message and message["tool_calls"]:
                    has_tool_call = True
                    collected_tool_calls = message["tool_calls"]

        # ✅ 流式结束后处理工具调用（此时 last_llm_sequence 已设置）
        if has_tool_call and collected_tool_calls:
            # 转换工具调用为 ADK 格式
            function_calls = []
            for tool_call in collected_tool_calls:
                # Ollama 格式: {"function": {"name": "...", "arguments": {...}}}
                function_info = tool_call.get("function", {})
                tool_name = function_info.get("name", "")

                function_call = FunctionCall(
                    name=tool_name,
                    args=function_info.get("arguments", {})
                )
                function_calls.append(function_call)

            # 创建包含工具调用的响应
            if function_calls:
                parts = []
                for fc in function_calls:
                    parts.append(Part(function_call=fc))

                response_content = Content(role="model", parts=parts)
                adk_response = LlmResponse(
                    content=response_content,
                    turn_complete=True,  # 工具调用表示一轮完成
                    finish_reason="STOP",
                    usage_metadata=usage_metadata  # ✅ 添加 token 统计
                )
                yield adk_response

        # ✅ 流式结束：如果没有工具调用，返回一个完成标记（包含 usage_metadata）
        elif accumulated_content and not has_tool_call:
            final_response = LlmResponse(
                content=Content(role="model", parts=[Part(text="")]),  # 空内容，仅作为结束标记
                turn_complete=True,
                finish_reason="STOP",
                usage_metadata=usage_metadata  # ✅ 添加 token 统计
            )
            yield final_response

        # ============ 步骤 3：如果没有流式内容，返回完整响应（降级） ============
        if not accumulated_content:
            our_response = await self.our_client.chat(
                messages=our_messages,
                system_prompt=None,
                tools=None,
                stream=False
            )
            adk_response = self._convert_response_to_adk_format(our_response)
            yield adk_response

    def _extract_tools_from_request(self, request: LlmRequest) -> Optional[List[Dict[str, Any]]]:
        """
        从 ADK LlmRequest 提取工具定义

        ADK 格式：request.config.tools = [Tool(function_declarations=[...])]
        Ollama 格式：[{"type": "function", "function": {...}}]
        """
        if not hasattr(request, 'config') or not request.config:
            return None

        if not hasattr(request.config, 'tools') or not request.config.tools:
            return None

        our_tools = []

        for tool in request.config.tools:
            if hasattr(tool, 'function_declarations'):
                for func_decl in tool.function_declarations:
                    # 转换 Schema 为 JSON Schema
                    parameters = self._convert_schema_to_json(func_decl.parameters) if hasattr(func_decl, 'parameters') else {                    }

                    our_tools.append({
                        "type": "function",
                        "function": {
                            "name": func_decl.name,
                            "description": func_decl.description or "",
                            "parameters": parameters
                        }
                    })

        return our_tools if our_tools else None

    def _convert_schema_to_json(self, schema: Any) -> Dict[str, Any]:
        """
        转换 ADK Schema 为 JSON Schema

        ADK Schema.type 是枚举，需要转换为字符串
        """
        if not schema:
            return {}

        result = {}

        # Type
        if hasattr(schema, 'type'):
            result['type'] = schema.type.name.lower() if hasattr(schema.type, 'name') else str(schema.type)

        # Properties
        if hasattr(schema, 'properties') and schema.properties:
            result['properties'] = {}
            for key, prop_schema in schema.properties.items():
                result['properties'][key] = self._convert_schema_to_json(prop_schema)

        # Required
        if hasattr(schema, 'required') and schema.required:
            result['required'] = list(schema.required)

        # Description
        if hasattr(schema, 'description') and schema.description:
            result['description'] = schema.description

        return result

    def _convert_request_to_our_format(self, request: LlmRequest) -> list:
        """
        转换 ADK LlmRequest 到我们的消息格式

        ADK request.contents 是 List[Content]
        我们的格式是 List[Dict[str, str]]

        ✅ 需要处理：
        1. 文本内容（Part.text）
        2. 工具调用（Part.function_call）
        3. 工具结果（Part.function_response 或 role="tool"）
        """
        our_messages = []

        # ADK 的 Content 对象包含 role 和 parts
        for content in request.contents:
            role = content.role if hasattr(content, 'role') else 'user'

            # ✅ 处理不同类型的 parts
            if not hasattr(content, 'parts'):
                continue

            message_data = {"role": role}
            text_parts = []
            tool_calls = []
            tool_result = None

            for part in content.parts:
                # 文本内容
                if hasattr(part, 'text') and part.text:
                    text_parts.append(part.text)

                # 工具调用（Assistant 消息）
                elif hasattr(part, 'function_call') and part.function_call:
                    import json
                    fc = part.function_call
                    # ✅ Ollama 期望 arguments 是 JSON 字符串（或字典，取决于实现）
                    args = fc.args if isinstance(fc.args, dict) else {}
                    tool_calls.append({
                        "id": f"call_{len(tool_calls)}",
                        "type": "function",
                        "function": {
                            "name": fc.name,
                            "arguments": args  # 保持字典格式
                        }
                    })

                # 工具结果（Tool 消息）
                elif hasattr(part, 'function_response') and part.function_response:
                    fr = part.function_response
                    # ✅ 提取字符串形式的结果
                    result_str = fr.response if hasattr(fr, 'response') else str(fr)
                    # 如果是字典，转换为 JSON 字符串
                    if isinstance(result_str, dict):
                        import json
                        result_str = json.dumps(result_str, ensure_ascii=False)
                    tool_result = {
                        "name": fr.name if hasattr(fr, 'name') else "",
                        "content": result_str
                    }

            # 构造消息
            if tool_calls:
                # Assistant 消息 + 工具调用
                message_data["content"] = ' '.join(text_parts) if text_parts else ""
                message_data["tool_calls"] = tool_calls
            elif tool_result:
                # Tool 结果消息
                message_data["role"] = "tool"
                message_data["content"] = tool_result["content"]
                message_data["tool_call_id"] = "call_0"  # Ollama 需要这个字段
            else:
                # 普通文本消息
                message_data["content"] = ' '.join(text_parts)

            our_messages.append(message_data)

        # ✅ 合并连续的同角色文本消息（避免流式 chunks 产生大量重复消息）
        merged_messages = []
        for msg in our_messages:
            # 如果是带工具的消息，直接添加
            if "tool_calls" in msg or msg.get("role") == "tool":
                merged_messages.append(msg)
                continue

            # 尝试与前一条消息合并
            if merged_messages and merged_messages[-1].get("role") == msg.get("role") \
                    and "tool_calls" not in merged_messages[-1]:
                # 合并文本内容
                merged_messages[-1]["content"] += msg.get("content", "")
            else:
                # 新消息
                merged_messages.append(msg)

        return merged_messages

    def _create_streaming_response(self, content: str) -> LlmResponse:
        """
        创建流式响应（ADK LlmResponse 格式）

        Args:
            content: 累积的文本内容

        Returns:
            LlmResponse 对象（流式，turn_complete=False）
        """
        response_content = Content(
            role="model",
            parts=[Part(text=content)]
        )

        return LlmResponse(
            content=response_content,
            turn_complete=False,  # ✅ 流式中，每个块都是 incomplete
            finish_reason=None
        )

    def _convert_response_to_adk_format(self, our_response: dict) -> LlmResponse:
        """
        转换我们的响应到 ADK LlmResponse 格式

        我们的响应：{"content": "...", "tool_calls": [...]}
        ADK 响应：LlmResponse 对象
        """
        # 创建 ADK 的 Content 对象
        content_parts = []

        # 添加文本内容
        if "content" in our_response and our_response["content"]:
            content_parts.append(Part(text=our_response["content"]))

        # 添加工具调用（如果有）
        if "tool_calls" in our_response and our_response["tool_calls"]:
            # ✅ 转换工具调用格式到 ADK FunctionCall
            for tool_call in our_response["tool_calls"]:
                # Ollama 格式: {"function": {"name": "...", "arguments": {...}}}
                function_info = tool_call.get("function", {})
                function_call = FunctionCall(
                    name=function_info.get("name", ""),
                    args=function_info.get("arguments", {})
                )
                content_parts.append(Part(function_call=function_call))

        # 创建 Content 对象
        response_content = Content(
            role="model",
            parts=content_parts
        )

        # 创建 LlmResponse
        # ✅ 使用正确的字段结构
        adk_response = LlmResponse(
            content=response_content,  # ✅ Content 对象
            turn_complete=True,  # ✅ 表示这一轮对话完成
            finish_reason="STOP"  # ✅ 完成原因（ADK 会通过 parts 检测 FunctionCall）
        )

        return adk_response

    def _save_model_invocation(
        self,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        start_time: datetime,
        finish_reason: Optional[str] = None
    ) -> Optional[int]:
        """
        保存 ModelInvocation 记录到数据库

        Args:
            prompt_tokens: 输入token数
            completion_tokens: 输出token数
            total_tokens: 总token数
            start_time: 开始时间
            finish_reason: 完成原因

        Returns:
            保存的序号，如果保存失败则返回 None
        """
        # 检查是否有必要的信息
        if not hasattr(self, 'db_session') or not self.db_session:
            LOGGER.debug("没有 db_session，跳过保存 ModelInvocation")
            return None

        if not hasattr(self, 'current_message_id') or not self.current_message_id:
            LOGGER.debug("没有 current_message_id，跳过保存 ModelInvocation")
            return None

        if not hasattr(self, 'current_session_id') or not self.current_session_id:
            LOGGER.debug("没有 current_session_id，跳过保存 ModelInvocation")
            return None

        try:
            # 导入 ModelInvocation（延迟导入避免循环依赖）
            from app.models.invocation import ModelInvocation

            # 递增序号
            if not hasattr(self, 'llm_sequence_counter'):
                object.__setattr__(self, 'llm_sequence_counter', 0)

            current_sequence = self.llm_sequence_counter + 1
            object.__setattr__(self, 'llm_sequence_counter', current_sequence)

            # 计算耗时
            duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # 创建记录
            invocation = ModelInvocation(
                message_id=str(self.current_message_id),
                session_id=str(self.current_session_id),
                sequence_number=current_sequence,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
                model_name=self.model_name,
                finish_reason=finish_reason,
                created_at=datetime.utcnow()
            )

            # 保存到数据库
            self.db_session.add(invocation)
            self.db_session.flush()  # 立即写入，但不提交（由外层控制提交）

            LOGGER.info(
                f"✅ 已保存 ModelInvocation 记录 #{current_sequence}: "
                f"tokens={total_tokens}, duration={duration_ms}ms"
            )

            return current_sequence

        except Exception as e:
            LOGGER.error(f"保存 ModelInvocation 记录失败: {e}", exc_info=True)
            # 不抛出异常，避免影响正常流程
            return None

    def connect(self):
        """
        连接到 LLM 服务（如果需要）

        我们的客户端通常在初始化时就连接了，所以这里可以为空
        """
        return None

    @classmethod
    def supported_models(cls) -> list[str]:
        """
        返回支持的模型列表

        这个方法是 BaseLlm 要求的
        """
        return [
            "qwen:8b",
            "qwen:14b",
            "qwen3:8b",
            "openai:gpt-4",
            "openai:gpt-3.5-turbo"
        ]


# ============ 工厂函数 ============
def create_adk_llm_from_our_client(our_client: BaseAIClient, model_name: str) -> ADKLlmAdapter:
    """
    工厂函数：从我们的客户端创建 ADK LLM 适配器

    Args:
        our_client: 我们的 BaseAIClient 实例
        model_name: 模型名称

    Returns:
        ADKLlmAdapter 实例

    Example:
        >>> from app.ai.clients.qwen_client import QwenClient
        >>> from app.ai.factory import FACTORY
        >>>
        >>> our_client = FACTORY.create_client("ollama", "qwen3:8b", "http://localhost:11434")
        >>> adk_llm = create_adk_llm_from_our_client(our_client, "qwen3:8b")
        >>>
        >>> # 现在可以传给 ADK Agent
        >>> from google.adk import Agent
        >>> agent = Agent(name="test", model=adk_llm)
    """
    return ADKLlmAdapter(our_client=our_client, model_name=model_name)

