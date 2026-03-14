"""CLI 端到端测试配置"""

import pytest

from ncatbot.utils import ncatbot_config


@pytest.fixture
def cli_test_env(tmp_path):
    """创建 CLI 测试环境

    提供一个隔离的临时目录用于测试，
    自动设置插件目录并在测试后清理。
    """
    # 保存原始配置
    original_plugins_dir = ncatbot_config.plugin.plugins_dir

    # 设置临时插件目录
    plugins_dir = tmp_path / "plugins"
    plugins_dir.mkdir()
    ncatbot_config.plugin.plugins_dir = str(plugins_dir)

    yield {
        "tmp_path": tmp_path,
        "plugins_dir": plugins_dir,
        "config": ncatbot_config,
    }

    # 恢复原始配置
    ncatbot_config.plugin.plugins_dir = original_plugins_dir


@pytest.fixture
def sample_plugin_in_env(cli_test_env):
    """在测试环境中创建一个示例插件"""
    plugins_dir = cli_test_env["plugins_dir"]
    plugin_dir = plugins_dir / "sample_plugin"
    plugin_dir.mkdir()

    # 创建 manifest.toml
    manifest = plugin_dir / "manifest.toml"
    manifest.write_text(
        """name = "sample_plugin"
version = "1.0.0"
author = "Test Author"
description = "A sample plugin for testing"
main = "plugin.py"
""",
        encoding="utf-8",
    )

    # 创建 plugin.py
    plugin_py = plugin_dir / "plugin.py"
    plugin_py.write_text(
        """from ncatbot.plugin_system import NcatBotPlugin

class SamplePlugin(NcatBotPlugin):
    pass
""",
        encoding="utf-8",
    )

    # 创建 __init__.py
    init_py = plugin_dir / "__init__.py"
    init_py.write_text("from .plugin import SamplePlugin\n", encoding="utf-8")

    return plugin_dir
