"""
废弃代码移除规则
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..base import MigrationRule


class RemoveDeprecatedCodeRule(MigrationRule):
    """
    删除废弃代码规则

    用于删除已废弃的导入和语句，如 CompatibleEnrollment 相关代码。
    """

    def __init__(
        self,
        name: str,
        description: str,
        deprecated_imports: Optional[Dict[str, Set[str]]] = None,
        deprecated_assignments: Optional[Set[str]] = None,
    ):
        """
        Args:
            name: 规则名称
            description: 规则描述
            deprecated_imports: 废弃的导入 {模块路径: {符号名称集合}}
            deprecated_assignments: 废弃的赋值语句模式 (如 "bot = CompatibleEnrollment")
        """
        self._name = name
        self._description = description
        self.deprecated_imports = deprecated_imports or {}
        self.deprecated_assignments = deprecated_assignments or set()

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        changes: List[str] = []
        lines = content.split("\n")
        new_lines: List[str] = []
        i = 0

        while i < len(lines):
            line = lines[i]
            skip_line = False

            # 检查是否是废弃的导入语句
            for module, symbols in self.deprecated_imports.items():
                # 匹配 from module import xxx, yyy
                import_match = re.match(
                    rf"^(\s*)from\s+{re.escape(module)}\s+import\s+(.+)$", line
                )
                if import_match:
                    indent = import_match.group(1)
                    imports_str = import_match.group(2).strip()

                    # 处理括号包裹的多行导入
                    if imports_str.startswith("(") and ")" not in imports_str:
                        # 多行导入，收集所有行
                        full_imports = imports_str[1:]  # 去掉开头的 (
                        i += 1
                        while i < len(lines) and ")" not in lines[i]:
                            full_imports += lines[i]
                            i += 1
                        if i < len(lines):
                            full_imports += lines[i].split(")")[0]
                        imports_str = full_imports

                    # 解析导入的符号
                    if imports_str.startswith("("):
                        imports_str = imports_str[1:]
                    if imports_str.endswith(")"):
                        imports_str = imports_str[:-1]

                    import_names = [
                        n.strip().split(" as ")[0].strip()
                        for n in imports_str.split(",")
                        if n.strip()
                    ]

                    # 过滤掉废弃的符号
                    kept_names = [n for n in import_names if n not in symbols]
                    removed_names = [n for n in import_names if n in symbols]

                    if removed_names:
                        changes.append(f"移除废弃导入: {', '.join(removed_names)}")

                    if kept_names:
                        # 还有其他需要保留的导入
                        new_lines.append(
                            f"{indent}from {module} import {', '.join(kept_names)}"
                        )
                    # 如果没有保留的导入，则整行删除
                    skip_line = True
                    break

            # 检查是否是废弃的赋值语句
            if not skip_line:
                for pattern in self.deprecated_assignments:
                    if re.match(rf"^\s*{re.escape(pattern)}\s*$", line):
                        changes.append(f"移除废弃语句: {pattern}")
                        skip_line = True
                        break

            if not skip_line:
                new_lines.append(line)

            i += 1

        new_content = "\n".join(new_lines)
        return new_content, changes


class SelectiveImportRemovalRule(MigrationRule):
    """
    选择性导入移除规则

    从导入语句中移除特定的符号，同时保留其他符号。
    适用于移除废弃但与其他有效符号在同一导入语句中的情况。
    """

    def __init__(
        self,
        name: str,
        description: str,
        module: str,
        remove_symbols: Set[str],
    ):
        """
        Args:
            name: 规则名称
            description: 规则描述
            module: 导入模块路径
            remove_symbols: 需要移除的符号集合
        """
        self._name = name
        self._description = description
        self.module = module
        self.remove_symbols = remove_symbols

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        changes: List[str] = []

        # 匹配单行导入
        pattern = rf"^(\s*)from\s+{re.escape(self.module)}\s+import\s+([^(\n]+)$"

        def process_import(match: re.Match) -> str:
            indent = match.group(1)
            imports_str = match.group(2).strip()

            # 解析导入的符号
            import_items = [n.strip() for n in imports_str.split(",") if n.strip()]

            kept_items = []
            removed_items = []

            for item in import_items:
                # 获取原始符号名（处理 as 别名）
                original_name = item.split(" as ")[0].strip()
                if original_name in self.remove_symbols:
                    removed_items.append(original_name)
                else:
                    kept_items.append(item)

            if removed_items:
                changes.append(f"移除废弃符号: {', '.join(removed_items)}")

            if kept_items:
                return f"{indent}from {self.module} import {', '.join(kept_items)}"
            else:
                # 所有符号都被移除，删除整行
                return ""

        new_content = re.sub(pattern, process_import, content, flags=re.MULTILINE)

        # 清理可能产生的空行（连续多个空行变成一个）
        new_content = re.sub(r"\n{3,}", "\n\n", new_content)

        return new_content, changes
