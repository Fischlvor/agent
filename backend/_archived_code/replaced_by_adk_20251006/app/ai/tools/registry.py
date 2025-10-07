"""工具注册表模块。"""

import importlib
import inspect
import logging
import pkgutil
from typing import Any, Dict, List, Optional, Type

from .base import BaseTool

LOGGER = logging.getLogger(__name__)


class ToolRegistry:
    """工具注册表，用于管理和注册所有可用工具"""

    def __init__(self):
        self._tools: Dict[str, Type[BaseTool]] = {}
        self._instances: Dict[str, BaseTool] = {}

    def register(self, tool_class: Type[BaseTool]) -> None:
        """
        注册工具类

        Args:
            tool_class: 工具类，必须是BaseTool的子类
        """
        if not inspect.isclass(tool_class) or not issubclass(
                tool_class, BaseTool):
            raise TypeError(f"工具必须是BaseTool的子类: {tool_class}")

        tool_name = tool_class.get_name()
        if tool_name in self._tools:
            LOGGER.warning("工具 '%s' 已被注册，将被覆盖", tool_name)

        self._tools[tool_name] = tool_class
        LOGGER.info("工具 '%s' 已注册", tool_name)

    def unregister(self, tool_name: str) -> None:
        """
        取消注册工具

        Args:
            tool_name: 工具名称
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            if tool_name in self._instances:
                del self._instances[tool_name]
            LOGGER.info("工具 '%s' 已取消注册", tool_name)
        else:
            LOGGER.warning("工具 '%s' 未注册，无法取消注册", tool_name)

    def get_tool(self, tool_name: str) -> Optional[Type[BaseTool]]:
        """
        获取工具类

        Args:
            tool_name: 工具名称

        Returns:
            工具类，如果不存在则返回None
        """
        return self._tools.get(tool_name)

    def get_instance(self, tool_name: str) -> Optional[BaseTool]:
        """
        获取工具实例

        Args:
            tool_name: 工具名称

        Returns:
            工具实例，如果不存在则返回None
        """
        if tool_name not in self._instances and tool_name in self._tools:
            self._instances[tool_name] = self._tools[tool_name]()

        return self._instances.get(tool_name)

    def get_all_tools(self) -> Dict[str, Type[BaseTool]]:
        """
        获取所有注册的工具类

        Returns:
            工具名称到工具类的映射
        """
        return self._tools.copy()

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的JSON Schema定义

        Returns:
            工具的JSON Schema定义列表
        """
        return [tool_class.get_schema() for tool_class in self._tools.values()]

    def auto_discover(self, package_name: str) -> None:
        """
        自动发现并注册指定包中的所有工具

        Args:
            package_name: 包名，如 'app.ai.tools.general'
        """
        try:
            package = importlib.import_module(package_name)

            for _, module_name, is_pkg in pkgutil.iter_modules(
                    package.__path__, package.__name__ + "."):
                if is_pkg:
                    # 如果是子包，递归处理
                    self.auto_discover(module_name)
                else:
                    # 如果是模块，导入并查找工具类
                    try:
                        module = importlib.import_module(module_name)
                        for name, obj in inspect.getmembers(module):
                            if (inspect.isclass(obj)
                                    and issubclass(obj, BaseTool)
                                    and obj != BaseTool
                                    and not name.startswith("_")):
                                self.register(obj)
                    except Exception as e:
                        LOGGER.error("导入模块 %s 时出错: %s", module_name, str(e))
        except Exception as e:
            LOGGER.error("自动发现工具时出错: %s", str(e))


# 全局工具注册表实例
REGISTRY = ToolRegistry()
