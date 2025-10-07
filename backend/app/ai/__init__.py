"""AI模块，提供Agent服务和AI客户端工厂。"""

from .factory import FACTORY as factory
# from .function_calling import HANDLER as function_calling_handler  # ✅ 已由 ADK 内置功能替代
# from .tools.executor import EXECUTOR as tool_executor  # ✅ 已由 ADK 内置功能替代
# from .tools.registry import REGISTRY as tool_registry  # ✅ 已由 mcp_tools_adapter 替代

__all__ = [
    "factory",
    # "function_calling_handler",  # ✅ 已由 ADK 内置功能替代
    # "tool_registry",  # ✅ 已由 adk_tools_adapter 替代
    # "tool_executor",  # ✅ 已由 ADK 内置功能替代
]
