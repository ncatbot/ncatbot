"""
废弃装饰器替换规则
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Set, Tuple

from ..base import MigrationRule


class DeprecatedDecoratorReplacementRule(MigrationRule):
    """
    废弃装饰器替换规则

    将废弃的 @bot.xxx_event 装饰器替换为新的 filter_system 装饰器。
    """

    def __init__(
        self,
        name: str = "deprecated_decorator_replacement",
        description: str = "将废弃的 @bot.xxx_event 装饰器替换为新的 filter_system 装饰器",
    ):
        self._name = name
        self._description = description
        # 装饰器映射：旧装饰器 -> (新装饰器列表, 需要导入的符号)
        self.decorator_mapping = {
            "notice_event": (["on_notice"], ["on_notice"]),
            "private_event": (
                ["on_message", "private_filter"],
                ["on_message", "private_filter"],
            ),
            "group_event": (
                ["on_message", "group_filter"],
                ["on_message", "group_filter"],
            ),
            "request_event": (["on_request"], ["on_request"]),
        }
        self.import_module = (
            "ncatbot.core.service.builtin.unified_registry.filter_system"
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        changes: List[str] = []
        needed_imports: Set[str] = set()

        # 匹配 @bot.xxx_event 或 @任意变量.xxx_event
        # 这里我们匹配常见的模式：@bot.xxx_event, @enrollment.xxx_event 等
        pattern = r"^(\s*)@(\w+)\.(\w+_event)\s*$"

        def replace_decorator(match: re.Match) -> str:
            indent = match.group(1)
            var_name = match.group(2)  # bot, enrollment 等
            event_type = match.group(3)  # notice_event, private_event 等

            if event_type in self.decorator_mapping:
                new_decorators, imports = self.decorator_mapping[event_type]
                needed_imports.update(imports)
                changes.append(
                    f"装饰器替换: @{var_name}.{event_type} -> @{' @'.join(new_decorators)}"
                )
                # 生成新的装饰器
                return "\n".join(f"{indent}@{dec}" for dec in new_decorators)
            else:
                # 未知的事件类型，保持原样
                return match.group(0)

        new_content = re.sub(pattern, replace_decorator, content, flags=re.MULTILINE)

        # 如果有需要导入的符号，添加导入语句
        if needed_imports and new_content != content:
            # 检查是否已有相关导入
            existing_imports = set()
            import_pattern = rf"from\s+{re.escape(self.import_module)}\s+import\s+(.+)"
            import_match = re.search(import_pattern, content)
            if import_match:
                existing = import_match.group(1)
                existing_imports = {s.strip() for s in existing.split(",")}

            # 计算需要新增的导入
            new_imports = needed_imports - existing_imports

            if new_imports:
                # 查找合适的位置添加导入
                # 在所有导入语句之后（包括多行导入）
                lines = new_content.split("\n")
                insert_idx = 0
                in_multiline_import = False

                for i, line in enumerate(lines):
                    stripped = line.strip()

                    # 检测多行导入的开始
                    if (
                        (stripped.startswith("from ") or stripped.startswith("import "))
                        and "(" in stripped
                        and ")" not in stripped
                    ):
                        in_multiline_import = True
                        continue

                    # 检测多行导入的结束
                    if in_multiline_import:
                        if ")" in stripped:
                            in_multiline_import = False
                            insert_idx = i + 1
                        continue

                    # 单行导入语句
                    if stripped.startswith("import ") or stripped.startswith("from "):
                        insert_idx = i + 1
                    elif (
                        stripped
                        and not stripped.startswith("#")
                        and insert_idx > 0
                        and not in_multiline_import
                    ):
                        # 遇到非导入、非注释、非空行，且不在多行导入中，停止搜索
                        break

                # 插入新的导入语句
                import_line = (
                    f"from {self.import_module} import {', '.join(sorted(new_imports))}"
                )
                lines.insert(insert_idx, import_line)
                new_content = "\n".join(lines)
                changes.append(f"添加导入: {', '.join(sorted(new_imports))}")

        return new_content, changes
