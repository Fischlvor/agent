"""
前端事件适配器

将 Google ADK 事件转换为前端展示格式

功能：
- 提取文本内容（content）
- 提取思考内容（thinking）
- 提取工具调用（tool_call）
- 提取工具结果（tool_result）

注意：这不是真正的 MCP 协议（工具调用），只是用于前端展示的格式转换
"""

from typing import Dict, Any, AsyncIterator, Optional
import re
import uuid


class FrontendEventAdapter:
    """ADK 事件 → 前端展示格式转换器"""

    def __init__(self, debug: bool = False):
        self.debug = debug

    async def convert_adk_event_stream(
        self,
        adk_event: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        转换 ADK 事件为前端展示格式的流式事件

        Args:
            adk_event: ADK Event 对象

        Yields:
            前端展示格式的事件字典
        """
        if self.debug:
            event_type = type(adk_event).__name__
            print(f"[ADK→Frontend] {event_type}")

        # ✅ 一次处理所有内容（文本 + 工具调用都在 content.parts 里）
        if hasattr(adk_event, 'content') and adk_event.content:
            # 处理文本内容
            mcp_event = self._convert_content_event(adk_event)
            if mcp_event:
                yield mcp_event

            # 处理工具调用（如果有 FunctionCall parts）
            async for tool_event in self._extract_tool_calls(adk_event):
                yield tool_event

    def _convert_content_event(self, adk_event: Any) -> Optional[Dict[str, Any]]:
        """
        转换文本内容事件

        ✅ 简化逻辑（基于测试）：
        - 直接拼接 parts 中的文本
        - 简单的思考标签检测
        """
        content = adk_event.content

        if not hasattr(content, 'parts') or not content.parts:
            return None

        # ✅ 直接拼接文本（列表推导式）
        text = ''.join(
            part.text for part in content.parts
            if hasattr(part, 'text') and part.text
        )

        if not text:
            return None

        # ✅ 简单的思考标签检测
        # 如果包含完整的 <think>...</think>，提取第一个
        if '<think>' in text and '</think>' in text:
            match = re.search(r'<think>(.*?)</think>', text, re.DOTALL)
            if match:
                thinking_text = match.group(1).strip()
                if thinking_text:
                    return {
                        "type": "thinking",
                        "delta": thinking_text,
                        "title": "思考中"
                    }

                # 移除思考标签，返回普通内容
                text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        # 返回普通内容
        if text:
            return {
                "type": "content",
                "delta": text
            }

        return None

    async def _extract_tool_calls(self, adk_event: Any) -> AsyncIterator[Dict[str, Any]]:
        """
        提取工具调用和工具结果

        ✅ 处理：
        1. FunctionCall → tool_call 事件
        2. FunctionResponse → tool_result 事件
        """
        content = adk_event.content

        if not hasattr(content, 'parts'):
            return

        # ✅ 处理 FunctionCall 和 FunctionResponse
        for part in content.parts:
            # 工具调用
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                yield {
                    "type": "tool_call",
                    "tool_call": {
                        "id": str(uuid.uuid4()),
                        "name": getattr(fc, 'name', ''),
                        "arguments": getattr(fc, 'args', {})
                    }
                }

            # ✅ 工具结果
            elif hasattr(part, 'function_response') and part.function_response:
                fr = part.function_response
                yield {
                    "type": "tool_result",
                    "tool_result": {
                        "id": str(uuid.uuid4()),
                        "name": getattr(fr, 'name', ''),  # ✅ 提取工具名称
                        "result": getattr(fr, 'response', '')
                    }
                }


# ============ 工厂函数 ============

def create_frontend_event_adapter(debug: bool = False) -> FrontendEventAdapter:
    """
    创建前端事件适配器

    Args:
        debug: 是否启用调试模式

    Returns:
        FrontendEventAdapter 实例
    """
    return FrontendEventAdapter(debug=debug)


# ============ 向后兼容的别名 ============
# 保持旧名字的兼容性
ADKToMCPAdapter = FrontendEventAdapter
create_adk_to_mcp_adapter = create_frontend_event_adapter
