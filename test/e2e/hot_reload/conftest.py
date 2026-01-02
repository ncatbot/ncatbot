"""
热重载测试共享 fixtures
"""

import pytest
import re
import sys
import time
from pathlib import Path
from typing import Dict, Optional

from ncatbot.utils.testing import E2ETestSuite

# 测试插件目录
FIXTURES_DIR = Path(__file__).parent / "fixtures"
PLUGINS_DIR = FIXTURES_DIR / "plugins"
RELOAD_PLUGIN_DIR = PLUGINS_DIR / "reload_test_plugin"
RELOAD_PLUGIN_MAIN = RELOAD_PLUGIN_DIR / "main.py"

# 原始文件内容的快照
_ORIGINAL_CONTENT = None

# 等待热重载完成的时间（需要足够长以确保稳定）
WAIT_TIME = 0.2


def _get_original_content() -> Optional[str]:
    """获取插件文件的原始内容"""
    global _ORIGINAL_CONTENT
    if _ORIGINAL_CONTENT is None and RELOAD_PLUGIN_MAIN.exists():
        content = RELOAD_PLUGIN_MAIN.read_text()
        # 检查是否是原始状态（MARKER_VALUE 和 COMMAND_RESPONSE 都是 original）
        is_original = (
            'MARKER_VALUE: str = "original"' in content and
            'COMMAND_RESPONSE: str = "original_response"' in content
        )
        if is_original:
            _ORIGINAL_CONTENT = content
        else:
            _ORIGINAL_CONTENT = _restore_original_content(content)
    return _ORIGINAL_CONTENT


def _restore_original_content(content: str) -> str:
    """将修改后的内容还原为原始状态"""
    content = content.replace('MARKER_VALUE: str = "modified"', 'MARKER_VALUE: str = "original"')
    content = content.replace('version = "1.0.1"', 'version = "1.0.0"')
    content = re.sub(r'MARKER_VALUE: str = "modified_\d+"', 'MARKER_VALUE: str = "original"', content)
    # 还原命令响应
    content = content.replace('COMMAND_RESPONSE: str = "modified_response"', 'COMMAND_RESPONSE: str = "original_response"')
    return content


def _reset_plugin_file():
    """重置插件文件到原始状态"""
    original = _get_original_content()
    if original:
        RELOAD_PLUGIN_MAIN.write_text(original)


def _cleanup_modules():
    """清理插件模块缓存"""
    modules_to_remove = [
        name for name in list(sys.modules.keys())
        if "reload_test_plugin" in name or "ncatbot_plugin" in name
    ]
    for name in modules_to_remove:
        sys.modules.pop(name, None)


def get_plugin_class(plugin_name: str):
    """从已加载的模块中获取插件类"""
    for module_name, module in sys.modules.items():
        if f"ncatbot_plugin." in module_name and module_name.endswith(".main"):
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and hasattr(attr, "name")
                    and getattr(attr, "name", None) == plugin_name
                ):
                    return attr
    return None


def modify_plugin_file(file_path: Path, replacements: Dict[str, str]) -> str:
    """修改插件文件内容"""
    content = file_path.read_text()
    for old, new in replacements.items():
        content = content.replace(old, new)
    file_path.write_text(content)
    return content


# 模块导入时初始化原始内容快照
_get_original_content()


@pytest.fixture
def test_suite():
    """创建测试套件（每个测试完全隔离）"""
    # 重置状态
    _cleanup_modules()
    _reset_plugin_file()
    
    suite = E2ETestSuite()
    suite.setup()
    
    # 暂停 watcher，防止检测到初始化阶段的文件操作
    file_watcher = suite.services.file_watcher
    file_watcher.pause()
    
    # 确保监视测试插件目录
    file_watcher.add_watch_dir(str(PLUGINS_DIR))
    
    suite.index_plugin(str(RELOAD_PLUGIN_DIR))
    
    # 等待初始扫描完成，清空 pending 队列，然后恢复
    with file_watcher._pending_lock:
        file_watcher._pending_dirs.clear()
    file_watcher.resume()
    
    yield suite
    
    # teardown 前暂停，防止检测到文件重置
    file_watcher.pause()
    suite.teardown()
    _cleanup_modules()
    _reset_plugin_file()


@pytest.fixture
def plugin_file():
    """提供插件文件路径"""
    return RELOAD_PLUGIN_MAIN
