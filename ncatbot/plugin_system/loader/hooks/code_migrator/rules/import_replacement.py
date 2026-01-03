"""
导入路径替换规则
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..base import MigrationRule


class ImportReplacementRule(MigrationRule):
    """导入路径替换规则"""

    def __init__(
        self,
        name: str,
        description: str,
        old_import: str,
        new_import: str,
        old_names: Optional[Dict[str, str]] = None,
    ):
        """
        Args:
            name: 规则名称
            description: 规则描述
            old_import: 旧的导入路径 (如 "ncatbot.core.event")
            new_import: 新的导入路径 (如 "ncatbot.core")
            old_names: 旧名称 -> 新名称 映射 (如 {"BaseMessageEvent": "MessageEvent"})
        """
        self._name = name
        self._description = description
        self.old_import = old_import
        self.new_import = new_import
        self.old_names = old_names or {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        changes: List[str] = []
        new_content = content

        # 处理 from ... import ... 语句
        new_content, import_changes = self._migrate_from_imports(new_content)
        changes.extend(import_changes)

        # 处理 import ... 语句
        new_content, import_changes = self._migrate_direct_imports(new_content)
        changes.extend(import_changes)

        # 处理代码中的符号名称替换
        new_content, name_changes = self._migrate_symbol_names(new_content)
        changes.extend(name_changes)

        return new_content, changes

    def _migrate_from_imports(self, content: str) -> Tuple[str, List[str]]:
        """迁移 from ... import ... 语句"""
        changes: List[str] = []

        # 匹配 from old_import import xxx, yyy, zzz
        pattern = rf"^(\s*)from\s+{re.escape(self.old_import)}\s+import\s+(.+)$"

        def replace_import(match: re.Match) -> str:
            indent = match.group(1)
            imports_str = match.group(2)

            # 解析导入的名称
            # 处理多行导入和带括号的导入
            imports_str = imports_str.strip()
            if imports_str.startswith("("):
                imports_str = imports_str[1:]
            if imports_str.endswith(")"):
                imports_str = imports_str[:-1]

            # 分割导入的名称
            import_names = [
                name.strip() for name in imports_str.split(",") if name.strip()
            ]

            # 替换旧名称
            new_names = []
            for name in import_names:
                # 处理 as 别名
                if " as " in name:
                    original, alias = name.split(" as ")
                    original = original.strip()
                    alias = alias.strip()
                    new_original = self.old_names.get(original, original)
                    if new_original != original:
                        changes.append(f"重命名: {original} -> {new_original}")
                    new_names.append(f"{new_original} as {alias}")
                else:
                    name = name.strip()
                    new_name = self.old_names.get(name, name)
                    if new_name != name:
                        changes.append(f"重命名: {name} -> {new_name}")
                    new_names.append(new_name)

            if self.old_import != self.new_import:
                changes.append(f"导入路径变更: {self.old_import} -> {self.new_import}")

            return f"{indent}from {self.new_import} import {', '.join(new_names)}"

        new_content = re.sub(pattern, replace_import, content, flags=re.MULTILINE)
        return new_content, changes

    def _migrate_direct_imports(self, content: str) -> Tuple[str, List[str]]:
        """迁移 import ... 语句"""
        changes: List[str] = []

        # 匹配 import old_import 或 import old_import as xxx
        pattern = rf"^(\s*)import\s+{re.escape(self.old_import)}(\s+as\s+\w+)?$"

        def replace_import(match: re.Match) -> str:
            indent = match.group(1)
            alias_part = match.group(2) or ""
            if self.old_import != self.new_import:
                changes.append(f"导入路径变更: {self.old_import} -> {self.new_import}")
            return f"{indent}import {self.new_import}{alias_part}"

        new_content = re.sub(pattern, replace_import, content, flags=re.MULTILINE)
        return new_content, changes

    def _migrate_symbol_names(self, content: str) -> Tuple[str, List[str]]:
        """迁移代码中的符号名称（不在导入语句中）"""
        changes: List[str] = []

        for old_name, new_name in self.old_names.items():
            # 使用词边界匹配，避免部分替换
            # 排除导入语句中的名称（已在上面处理过）
            pattern = rf"\b{re.escape(old_name)}\b"

            # 先检查是否存在匹配
            if re.search(pattern, content):
                # 统计替换次数
                count = len(re.findall(pattern, content))
                # 执行替换
                new_content = re.sub(pattern, new_name, content)
                if new_content != content:
                    changes.append(f"符号重命名: {old_name} -> {new_name} ({count}处)")
                    content = new_content

        return content, changes
