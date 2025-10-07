"""工具系统初始化

✅ ADK 集成后：
- REGISTRY -> 由 adk_tools_adapter 管理
- 工具通过 MCP 协议动态加载和调用
"""

from . import general
from .base import BaseTool

__all__ = ["BaseTool", "general"]
