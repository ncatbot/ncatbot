"""
插件配置服务高级集成测试

测试 PluginConfigService 的高级功能：
- 配置迁移
- 配置变更回调
- 边界情况
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import patch
import yaml

from ncatbot.core.service import ServiceManager
from ncatbot.core.service.builtin.plugin_config import PluginConfigService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_config_file():
    """创建临时配置文件"""
    fd, path = tempfile.mkstemp(suffix=".yaml")
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.unlink(path)


# =============================================================================
# 配置迁移集成测试
# =============================================================================


class TestConfigMigration:
    """配置迁移集成测试"""

    @pytest.mark.asyncio
    async def test_get_or_migrate_with_legacy_file(self, temp_config_file):
        """测试 get_or_migrate_config 处理旧版文件"""
        manager = ServiceManager()

        # 创建旧版配置文件
        legacy_file = Path(temp_config_file).parent / "legacy_plugin.yaml"
        legacy_data = {"api_key": "legacy_key", "enabled": True}
        with open(legacy_file, "w") as f:
            yaml.dump(legacy_data, f)

        try:
            with patch(
                "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
                temp_config_file,
            ):
                manager.register(PluginConfigService)
                await manager.load("plugin_config")

                config_service = manager.plugin_config

                # 调用 get_or_migrate_config
                wrapper = await config_service.get_or_migrate_config(
                    "legacy_plugin", legacy_file
                )

                # 旧版配置应该被迁移
                assert wrapper["api_key"] == "legacy_key"
                assert wrapper["enabled"] is True

                await manager.close_all()
        finally:
            if legacy_file.exists():
                legacy_file.unlink()

    @pytest.mark.asyncio
    async def test_get_or_migrate_without_legacy_file(self, temp_config_file):
        """测试 get_or_migrate_config 在没有旧版文件时"""
        manager = ServiceManager()

        nonexistent_file = Path("/nonexistent/path/plugin.yaml")

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 调用 get_or_migrate_config
            wrapper = await config_service.get_or_migrate_config(
                "new_plugin", nonexistent_file
            )

            # 应该返回空配置包装器
            assert len(wrapper) == 0

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_migration_does_not_overwrite_existing(self, temp_config_file):
        """测试迁移不覆盖已有配置"""
        manager = ServiceManager()

        # 创建旧版配置文件
        legacy_file = Path(temp_config_file).parent / "plugin.yaml"
        legacy_data = {"api_key": "legacy_key", "new_key": "new_value"}
        with open(legacy_file, "w") as f:
            yaml.dump(legacy_data, f)

        # 预先写入一些配置
        with open(temp_config_file, "w") as f:
            yaml.dump({"plugin_config": {"plugin": {"api_key": "existing_key"}}}, f)

        try:
            with patch(
                "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
                temp_config_file,
            ):
                manager.register(PluginConfigService)
                await manager.load("plugin_config")

                config_service = manager.plugin_config

                # 已有配置，不应该迁移
                wrapper = await config_service.get_or_migrate_config(
                    "plugin", legacy_file
                )

                # 已有的值应该保持
                assert wrapper["api_key"] == "existing_key"

                await manager.close_all()
        finally:
            if legacy_file.exists():
                legacy_file.unlink()


# =============================================================================
# 配置变更回调集成测试
# =============================================================================


class TestConfigChangeCallback:
    """配置变更回调集成测试"""

    @pytest.mark.asyncio
    async def test_callback_triggered_on_change(self, temp_config_file):
        """测试配置变更时触发回调"""
        manager = ServiceManager()
        callback_log = []

        def on_api_key_change(old, new):
            callback_log.append({"old": old, "new": new})

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 注册带回调的配置
            config_service.register_config(
                "plugin",
                "api_key",
                default_value="",
                on_change=on_api_key_change,
            )

            # 更新配置
            config_service.set("plugin", "api_key", "new_key")

            # 验证回调被调用
            assert len(callback_log) == 1
            assert callback_log[0]["old"] == ""
            assert callback_log[0]["new"] == "new_key"

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_callback_not_triggered_on_same_value(self, temp_config_file):
        """测试设置相同值不触发回调"""
        manager = ServiceManager()
        callback_log = []

        def on_change(old, new):
            callback_log.append({"old": old, "new": new})

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            config_service.register_config(
                "plugin", "key", default_value="value", on_change=on_change
            )

            # 设置相同的值
            config_service.set("plugin", "key", "value")

            # 回调不应该被调用
            assert len(callback_log) == 0

            await manager.close_all()


# =============================================================================
# 边界情况测试
# =============================================================================


class TestEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_empty_config_file(self, temp_config_file):
        """测试空配置文件"""
        # 创建空文件
        Path(temp_config_file).touch()

        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 应该正常工作
            config_service.set_atomic("plugin", "key", "value")
            assert config_service.get("plugin", "key") == "value"

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_nonexistent_config_file(self, temp_config_file):
        """测试不存在的配置文件"""
        # 删除文件
        os.unlink(temp_config_file)

        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 应该正常工作
            config_service.set_atomic("plugin", "key", "value")
            assert config_service.get("plugin", "key") == "value"

            await manager.close_all()

    @pytest.mark.asyncio
    async def test_special_characters_in_config(self, temp_config_file):
        """测试配置值中的特殊字符"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 测试各种特殊字符（避免并发问题，使用批量更新）
            special_values = {
                "key_spaces": "value with spaces",
                "key_chinese": "中文值",
                "key_emoji": "emoji 🎉",
                "key_quotes": "value'with'quotes",
            }

            wrapper = config_service.get_plugin_config_wrapper("plugin")
            wrapper.bulk_update(special_values)

            # 等待异步保存完成
            await asyncio.sleep(0.02)

            await manager.close_all()

        # 重新加载验证
        manager2 = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager2.register(PluginConfigService)
            await manager2.load("plugin_config")

            config_service = manager2.plugin_config

            for key, expected in special_values.items():
                actual = config_service.get("plugin", key)
                assert actual == expected, (
                    f"{key}: expected {expected!r}, got {actual!r}"
                )

            await manager2.close_all()

    @pytest.mark.asyncio
    async def test_complex_nested_config(self, temp_config_file):
        """测试复杂嵌套配置"""
        manager = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager.register(PluginConfigService)
            await manager.load("plugin_config")

            config_service = manager.plugin_config

            # 复杂嵌套结构
            complex_value = {
                "level1": {"level2": {"level3": [1, 2, {"nested": "value"}]}},
                "list": [{"a": 1}, {"b": 2}],
            }

            config_service.set_atomic("plugin", "complex", complex_value)

            await manager.close_all()

        # 重新加载验证
        manager2 = ServiceManager()

        with patch(
            "ncatbot.core.service.builtin.plugin_config.service.CONFIG_PATH",
            temp_config_file,
        ):
            manager2.register(PluginConfigService)
            await manager2.load("plugin_config")

            config_service = manager2.plugin_config

            loaded = config_service.get("plugin", "complex")
            assert loaded == complex_value

            await manager2.close_all()
