"""
符号重命名规则
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, List, Tuple

from ..base import MigrationRule


class SymbolRenameRule(MigrationRule):
    """纯符号重命名规则（不涉及导入路径变更）"""

    def __init__(
        self,
        name: str,
        description: str,
        renames: Dict[str, str],
    ):
        """
        Args:
            name: 规则名称
            description: 规则描述
            renames: 旧名称 -> 新名称 映射
        """
        self._name = name
        self._description = description
        self.renames = renames

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    def apply(self, content: str, file_path: Path) -> Tuple[str, List[str]]:
        changes: List[str] = []

        for old_name, new_name in self.renames.items():
            pattern = rf"\b{re.escape(old_name)}\b"
            if re.search(pattern, content):
                count = len(re.findall(pattern, content))
                content = re.sub(pattern, new_name, content)
                changes.append(f"符号重命名: {old_name} -> {new_name} ({count}处)")

        return content, changes
