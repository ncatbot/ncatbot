"""
pytest 插件 — 自动发现并参数化插件冒烟测试

用法: 在 conftest.py 中导入此模块，或通过 pytest --plugin-dir=examples/ 使用。

功能:
  - @pytest.mark.plugin(name="xxx") marker 支持
  - --plugin-dir CLI 选项
  - 自动参数化冒烟测试
"""

from __future__ import annotations

from pathlib import Path
from typing import List

import pytest

from ncatbot.testing.discovery import discover_testable_plugins


def pytest_addoption(parser):
    """注册 --plugin-dir 命令行选项"""
    parser.addoption(
        "--plugin-dir",
        action="store",
        default=None,
        help="插件根目录路径（用于自动发现插件冒烟测试）",
    )


def pytest_configure(config):
    """注册自定义 marker"""
    config.addinivalue_line(
        "markers",
        "plugin(name): 标记为特定插件的测试",
    )
    config.addinivalue_line(
        "markers",
        "plugin_names(names): 指定要加载的插件名列表",
    )
    config.addinivalue_line(
        "markers",
        "plugin_dir(dir): 指定插件目录名",
    )


@pytest.fixture
def plugin_dir(request) -> Path:
    """从 --plugin-dir 选项获取插件根目录"""
    opt = request.config.getoption("--plugin-dir", default=None)
    if opt is None:
        pytest.skip("需要 --plugin-dir 参数")
    return Path(opt).resolve()


def pytest_collection_modifyitems(config, items):
    """根据 --plugin-dir 过滤插件测试"""
    plugin_dir = config.getoption("--plugin-dir", default=None)
    if plugin_dir is None:
        return

    # 如果指定了 plugin-dir，则只运行带 @pytest.mark.plugin 的测试
    # 其他测试跳过
    for item in items:
        if "plugin" not in item.keywords and "plugin_names" not in item.keywords:
            item.add_marker(pytest.mark.skip(reason="不在 --plugin-dir 测试范围内"))


def get_testable_plugin_names(plugin_dir: str) -> List[str]:
    """辅助函数：获取目录下所有可测试插件名"""
    manifests = discover_testable_plugins(Path(plugin_dir))
    return [m.name for m in manifests]
