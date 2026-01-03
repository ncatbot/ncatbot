"""
绝对导入转相对导入规则
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

from ..base import MigrationRule


class AbsoluteToRelativeImportRule(MigrationRule):
    """
    绝对导入转相对导入规则

    将 from plugins.XXX.xxx import yyy 转换为相对导入 from .xxx import yyy
    适用于插件代码中错误使用绝对导入的情况。
    """

    def __init__(
        self,
        name: str = "absolute_to_relative_import",
        description: str = "将插件内的绝对导入转换为相对导入",
    ):
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        changes: List[str] = []

        # 获取插件目录名（file_path 应该在 plugins/PluginName/ 下）
        # 找到 plugins 目录并获取插件名
        parts = file_path.parts
        plugin_name = None
        plugins_idx = None

        for i, part in enumerate(parts):
            if part == "plugins" and i + 1 < len(parts):
                plugins_idx = i
                plugin_name = parts[i + 1]
                break

        if not plugin_name:
            return content, changes

        # 计算当前文件相对于插件根目录的深度
        if plugins_idx is not None:
            # 当前文件在插件目录下的路径深度
            file_depth = len(parts) - plugins_idx - 2  # -2 是 plugins 和 plugin_name

        # 匹配 from plugins.PluginName.xxx import yyy
        # 或 from plugins.PluginName import yyy
        pattern = rf"^(\s*)from\s+plugins\.{re.escape(plugin_name)}((?:\.\w+)*)\s+import\s+(.+)$"

        def replace_import(match: re.Match) -> str:
            indent = match.group(1)
            submodule = match.group(2)  # 如 .handlers.get_handler 或空字符串
            imports = match.group(3)

            # 根据文件深度计算相对导入前缀
            if file_depth == 0:
                # 文件在插件根目录，直接使用 .
                relative_prefix = "."
            else:
                # 文件在子目录中，需要向上回溯
                relative_prefix = "." * (file_depth)

            if submodule:
                # 有子模块路径
                new_import = (
                    f"{indent}from {relative_prefix}{submodule[1:]} import {imports}"
                )
            else:
                # 直接从插件根导入
                new_import = f"{indent}from {relative_prefix} import {imports}"

            old_import = (
                f"from plugins.{plugin_name}{submodule} import {imports.strip()}"
            )
            changes.append(f"绝对导入 -> 相对导入: {old_import}")
            return new_import

        new_content = re.sub(pattern, replace_import, content, flags=re.MULTILINE)
        return new_content, changes
