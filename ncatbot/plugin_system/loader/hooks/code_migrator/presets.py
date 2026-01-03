"""
代码迁移框架 - 预设迁移规则

这里定义了 ncatbot 项目的预设迁移规则，用于自动更新废弃的导入路径和符号名称。
"""

from __future__ import annotations

from .migrator import CodeMigrator
from .rules import (
    ImportReplacementRule,
    SelectiveImportReplacementRule,
    SymbolRenameRule,
    AbsoluteToRelativeImportRule,
    RemoveDeprecatedCodeRule,
    SelectiveImportRemovalRule,
    DeprecatedDecoratorReplacementRule,
)


def create_default_migrator() -> CodeMigrator:
    """
    创建包含默认迁移规则的迁移器

    当前包含的迁移规则:
    1. BaseMessageEvent -> MessageEvent (ncatbot.core.event -> ncatbot.core)
    2. NcatBotEvent 导入路径变更 (ncatbot.plugin_system.event -> ncatbot.core)
    3. NcatBotEvent 从 ncatbot.plugin_system 选择性迁移到 ncatbot.core
    4. MessageChain -> MessageArray 符号重命名
    5. 移除废弃的 CompatibleEnrollment 导入和 bot = CompatibleEnrollment 语句
    6. 将插件内的绝对导入转换为相对导入
    7. message_segment -> message_segments 导入路径修正
    """
    migrator = CodeMigrator()

    # 规则1: BaseMessageEvent -> MessageEvent
    # 导入路径: ncatbot.core.event -> ncatbot.core
    migrator.register_rule(
        ImportReplacementRule(
            name="BaseMessageEvent_to_MessageEvent",
            description="将 BaseMessageEvent 重命名为 MessageEvent，并更新导入路径",
            old_import="ncatbot.core.event",
            new_import="ncatbot.core",
            old_names={"BaseMessageEvent": "MessageEvent"},
        )
    )

    # 规则2: NcatBotEvent 导入路径变更
    # ncatbot.plugin_system.event -> ncatbot.core
    migrator.register_rule(
        ImportReplacementRule(
            name="NcatBotEvent_import_path",
            description="更新 NcatBotEvent 的导入路径",
            old_import="ncatbot.plugin_system.event",
            new_import="ncatbot.core",
            old_names={},
        )
    )

    # 规则3: NcatBotEvent 从 ncatbot.plugin_system 迁移到 ncatbot.core
    # 使用选择性迁移，只迁移 NcatBotEvent，保留其他导入
    migrator.register_rule(
        SelectiveImportReplacementRule(
            name="NcatBotEvent_from_plugin_system",
            description="仅将 NcatBotEvent 从 ncatbot.plugin_system 迁移到 ncatbot.core",
            old_import="ncatbot.plugin_system",
            new_import="ncatbot.core",
            target_names={"NcatBotEvent"},
            renames={},
        )
    )

    # 规则4: MessageChain -> MessageArray 符号重命名
    # ncatbot.core 中的 MessageChain 已重命名为 MessageArray
    migrator.register_rule(
        SymbolRenameRule(
            name="MessageChain_to_MessageArray",
            description="将 MessageChain 重命名为 MessageArray",
            renames={"MessageChain": "MessageArray"},
        )
    )

    # 规则5: 移除 CompatibleEnrollment 相关导入
    # CompatibleEnrollment 已完全弃用，应使用 filter_system 中的装饰器替代
    migrator.register_rule(
        SelectiveImportRemovalRule(
            name="remove_CompatibleEnrollment_import",
            description="移除废弃的 CompatibleEnrollment 导入",
            module="ncatbot.plugin",
            remove_symbols={"CompatibleEnrollment"},
        )
    )

    # 规则6: 移除 bot = CompatibleEnrollment 语句
    migrator.register_rule(
        RemoveDeprecatedCodeRule(
            name="remove_CompatibleEnrollment_assignment",
            description="移除废弃的 bot = CompatibleEnrollment 赋值语句",
            deprecated_imports={},
            deprecated_assignments={"bot = CompatibleEnrollment"},
        )
    )

    # 规则7: 将插件内的绝对导入转换为相对导入
    # from plugins.PluginName.xxx import yyy -> from .xxx import yyy
    migrator.register_rule(
        AbsoluteToRelativeImportRule(
            name="absolute_to_relative_import",
            description="将插件内的绝对导入转换为相对导入",
        )
    )

    # 规则8: 替换废弃的 @bot.xxx_event 装饰器
    # @bot.notice_event -> @on_notice
    # @bot.private_event -> @on_message @private_filter
    # @bot.group_event -> @on_message @group_filter
    migrator.register_rule(
        DeprecatedDecoratorReplacementRule(
            name="deprecated_decorator_replacement",
            description="将废弃的 @bot.xxx_event 装饰器替换为新的 filter_system 装饰器",
        )
    )

    # 规则9: message_segment -> message_segments 导入路径修正
    # ncatbot.core.event.message_segment 已重命名为 ncatbot.core.event.message_segments
    migrator.register_rule(
        ImportReplacementRule(
            name="message_segment_to_message_segments",
            description="将 message_segment 导入路径修正为 message_segments",
            old_import="ncatbot.core.event.message_segment",
            new_import="ncatbot.core.event.message_segments",
            old_names={},
        )
    )

    return migrator
