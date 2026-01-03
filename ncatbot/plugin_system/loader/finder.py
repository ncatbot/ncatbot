"""跨插件导入支持模块。

提供自定义的 MetaPathFinder 来支持插件间的相对导入，
如 `from ..another_plugin import xxx`。
"""

import sys
import importlib.util
import importlib.machinery
import importlib.abc
from pathlib import Path
from typing import Dict, Optional

from ncatbot.utils import get_log

LOG = get_log("PluginFinder")

# 顶级虚拟包名称
TOP_PACKAGE_NAME = "ncatbot_plugin"


class PluginPackageFinder(importlib.abc.MetaPathFinder):
    """自定义 MetaPathFinder，用于支持跨插件导入。

    当从一个插件中使用 `from ..another_plugin import xxx` 时，
    Python 需要能够找到 `ncatbot_plugin.another_plugin` 包。
    这个 Finder 负责解析这些跨插件的导入请求。

    支持两种路径注册方式：
    1. sanitized 名称（如 ACM -> ACM）
    2. 文件夹名称（如 acm -> 对应的插件路径）

    这样用户可以使用 `from ..acm.xxx` 或 `from ..ACM.xxx` 来导入。
    """

    def __init__(self):
        # sanitized 名称 -> 插件目录路径
        self._plugin_paths: Dict[str, str] = {}
        # 文件夹名称 -> sanitized 名称（支持通过文件夹名称查找）
        self._folder_to_sanitized: Dict[str, str] = {}

    def register_plugin(
        self, sanitized_name: str, plugin_path: str, folder_name: Optional[str] = None
    ):
        """注册一个插件的路径。

        Args:
            sanitized_name: 插件的 sanitized 名称（用于包名）
            plugin_path: 插件目录的绝对路径
            folder_name: 插件文件夹名称（可选，用于支持通过文件夹名导入）
        """
        self._plugin_paths[sanitized_name] = plugin_path
        LOG.debug("注册插件路径: %s -> %s", sanitized_name, plugin_path)

        # 同时注册文件夹名称映射（如果与 sanitized 名称不同）
        if folder_name and folder_name != sanitized_name:
            self._folder_to_sanitized[folder_name] = sanitized_name
            # 也直接注册文件夹名称到路径的映射
            self._plugin_paths[folder_name] = plugin_path
            LOG.debug("注册文件夹名映射: %s -> %s", folder_name, sanitized_name)

    def unregister_plugin(self, sanitized_name: str, folder_name: Optional[str] = None):
        """注销一个插件的路径。

        Args:
            sanitized_name: 插件的 sanitized 名称
            folder_name: 插件文件夹名称（可选）
        """
        self._plugin_paths.pop(sanitized_name, None)
        if folder_name:
            self._plugin_paths.pop(folder_name, None)
            self._folder_to_sanitized.pop(folder_name, None)

    def _resolve_plugin_path(self, name: str) -> Optional[str]:
        """解析插件名称到路径。

        支持 sanitized 名称和文件夹名称。
        """
        # 直接查找
        if name in self._plugin_paths:
            return self._plugin_paths[name]
        # 通过文件夹名称映射查找
        if name in self._folder_to_sanitized:
            sanitized = self._folder_to_sanitized[name]
            return self._plugin_paths.get(sanitized)
        return None

    def find_spec(self, fullname, path, target=None):
        """查找模块 spec。

        只处理 ncatbot_plugin.xxx 形式的导入。
        """
        if not fullname.startswith(f"{TOP_PACKAGE_NAME}."):
            return None

        parts = fullname.split(".")
        if len(parts) < 2:
            return None

        # 获取插件名称（第二部分，可能是 sanitized 名称或文件夹名称）
        plugin_name = parts[1]
        plugin_path = self._resolve_plugin_path(plugin_name)

        if plugin_path is None:
            return None

        # 构建子模块路径
        if len(parts) == 2:
            # 这是插件包本身: ncatbot_plugin.plugin_name
            return self._find_package_spec(fullname, plugin_path)
        else:
            # 这是插件内的子模块: ncatbot_plugin.plugin_name.submodule...
            return self._find_submodule_spec(fullname, plugin_path, parts[2:])

    def _find_package_spec(self, fullname: str, plugin_path: str):
        """查找插件包的 spec。"""
        # 检查是否有 __init__.py
        init_file = Path(plugin_path) / "__init__.py"
        if init_file.exists():
            return importlib.util.spec_from_file_location(
                fullname,
                str(init_file),
                submodule_search_locations=[plugin_path],
            )
        # 没有 __init__.py，创建命名空间包
        spec = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
        spec.submodule_search_locations = [plugin_path]
        return spec

    def _find_submodule_spec(
        self, fullname: str, plugin_path: str, submodule_parts: list
    ):
        """查找插件内子模块的 spec。"""
        submodule_path = Path(plugin_path)
        for part in submodule_parts[:-1]:
            submodule_path = submodule_path / part

        module_name = submodule_parts[-1]

        # 检查是否是包（目录）
        package_dir = submodule_path / module_name
        if package_dir.is_dir():
            init_file = package_dir / "__init__.py"
            if init_file.exists():
                return importlib.util.spec_from_file_location(
                    fullname,
                    str(init_file),
                    submodule_search_locations=[str(package_dir)],
                )
            # 命名空间包
            spec = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = [str(package_dir)]
            return spec

        # 检查是否是模块文件
        module_file = submodule_path / f"{module_name}.py"
        if module_file.exists():
            return importlib.util.spec_from_file_location(fullname, str(module_file))

        return None

    def get_registered_plugins(self) -> Dict[str, str]:
        """返回已注册的插件路径（用于调试）。"""
        return dict(self._plugin_paths)


# 全局 Finder 实例
_plugin_finder = PluginPackageFinder()
_finder_installed = False


def get_plugin_finder() -> PluginPackageFinder:
    """获取全局 Finder 实例。"""
    return _plugin_finder


def ensure_finder_installed():
    """确保自定义 Finder 已安装到 sys.meta_path。"""
    global _finder_installed
    if not _finder_installed:
        sys.meta_path.insert(0, _plugin_finder)
        _finder_installed = True
        LOG.debug("已安装插件包 Finder")


def register_plugin_path(
    sanitized_name: str, plugin_path: str, folder_name: Optional[str] = None
):
    """注册插件路径到全局 Finder。

    应该在插件索引阶段调用，以便其他插件在加载时可以导入它。
    """
    ensure_finder_installed()
    _plugin_finder.register_plugin(sanitized_name, plugin_path, folder_name)


def unregister_plugin_path(sanitized_name: str, folder_name: Optional[str] = None):
    """从全局 Finder 注销插件路径。"""
    _plugin_finder.unregister_plugin(sanitized_name, folder_name)
