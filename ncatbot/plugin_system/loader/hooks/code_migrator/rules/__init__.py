"""
代码迁移框架 - 内置迁移规则

提供各种迁移规则类，用于自动更新插件代码中的废弃导入和符号名称。
"""

from .import_replacement import ImportReplacementRule
from .selective_import_replacement import SelectiveImportReplacementRule
from .symbol_rename import SymbolRenameRule
from .absolute_to_relative import AbsoluteToRelativeImportRule
from .deprecated_code_removal import (
    RemoveDeprecatedCodeRule,
    SelectiveImportRemovalRule,
)
from .decorator_replacement import DeprecatedDecoratorReplacementRule

__all__ = [
    "ImportReplacementRule",
    "SelectiveImportReplacementRule",
    "SymbolRenameRule",
    "AbsoluteToRelativeImportRule",
    "RemoveDeprecatedCodeRule",
    "SelectiveImportRemovalRule",
    "DeprecatedDecoratorReplacementRule",
]
