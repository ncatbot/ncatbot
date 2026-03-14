"""CLI 测试共享 fixtures"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture
def temp_plugins_dir(tmp_path):
    """创建临时插件目录"""
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    return plugins_dir


@pytest.fixture
def mock_config(temp_plugins_dir):
    """Mock 配置对象"""
    config = MagicMock()
    config.bot_uin = "123456789"
    config.root = "987654321"
    config._default_bot_uin = "123456"
    config.debug = False

    # 插件配置
    config.plugin = MagicMock()
    config.plugin.plugins_dir = str(temp_plugins_dir)

    # NapCat 配置
    config.napcat = MagicMock()
    config.napcat.ws_uri = "ws://localhost:3001"
    config.napcat.webui_uri = "http://localhost:6099"

    config.save = MagicMock()
    return config


@pytest.fixture
def sample_plugin(temp_plugins_dir):
    """创建一个示例插件目录"""
    plugin_dir = temp_plugins_dir / "sample_plugin"
    plugin_dir.mkdir()

    # 创建 manifest.toml
    manifest = plugin_dir / "manifest.toml"
    manifest.write_text(
        """name = "sample_plugin"
version = "1.0.0"
author = "Test Author"
description = "A sample plugin for testing"
main = "plugin.py"
"""
    )

    # 创建 plugin.py
    plugin_py = plugin_dir / "plugin.py"
    plugin_py.write_text(
        """from ncatbot.plugin_system import NcatBotPlugin

class SamplePlugin(NcatBotPlugin):
    pass
"""
    )

    # 创建 __init__.py
    init_py = plugin_dir / "__init__.py"
    init_py.write_text("from .plugin import SamplePlugin\n")

    return plugin_dir


@pytest.fixture
def cli_registry():
    """获取一个干净的命令注册表"""
    from ncatbot.cli.commands.registry import CommandRegistry

    return CommandRegistry()
