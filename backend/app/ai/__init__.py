"""AI模块，提供Agent服务和AI客户端工厂。"""

from .factory import FACTORY as factory
from .function_calling import HANDLER as function_calling_handler
from .tools.executor import EXECUTOR as tool_executor
from .tools.registry import REGISTRY as tool_registry

__all__ = [
    "factory",
    "function_calling_handler",
    "tool_registry",
    "tool_executor",
]
