"""
插件数据持久化集成测试

测试插件在加载、运行、卸载过程中数据的持久化功能。
"""

import pytest
import pytest_asyncio
import tempfile
import json
from pathlib import Path

from ncatbot.core import EventBus
from ncatbot.core.service import ServiceManager
from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.plugin_system.loader import PluginLoader


# =============================================================================
# 测试插件
# =============================================================================


class DataPersistenceTestPlugin(NcatBotPlugin):
    """测试数据持久化的插件"""

    name = "data_test_plugin"
    version = "1.0.0"
    author = "Test"
    description = "测试插件数据持久化"

    async def on_load(self):
        """插件加载时读取和修改数据"""
        # 读取计数器
        counter = self.data.get("load_count", 0)
        self.data["load_count"] = counter + 1

        # 记录加载标记
        self.data["loaded"] = True
        self.data["plugin_name"] = self.name

    async def on_close(self):
        """插件卸载时修改数据"""
        self.data["closed"] = True
        close_count = self.data.get("close_count", 0)
        self.data["close_count"] = close_count + 1


class ComplexDataPlugin(NcatBotPlugin):
    """测试复杂数据结构的插件"""

    name = "complex_data_plugin"
    version = "1.0.0"
    author = "Test"
    description = "测试复杂数据结构"

    async def on_load(self):
        """设置复杂数据结构"""
        if not self.data:
            self.data["users"] = []
            self.data["settings"] = {}
            self.data["logs"] = []

        # 添加用户
        self.data["users"].append(
            {
                "id": len(self.data["users"]) + 1,
                "name": f"user_{len(self.data['users']) + 1}",
            }
        )

        # 更新设置
        self.data["settings"]["enabled"] = True
        self.data["settings"]["version"] = self.version

        # 添加日志
        self.data["logs"].append(f"Loaded at load_count={len(self.data['logs']) + 1}")


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest_asyncio.fixture
async def service_manager(temp_data_dir, monkeypatch):
    """创建服务管理器"""
    from ncatbot.core.service.builtin import (
        PluginConfigService,
        PluginDataService,
        UnifiedRegistryService,
    )
    from unittest.mock import MagicMock

    manager = ServiceManager()
    manager.set_test_mode(True)

    # 模拟 bot_client 和 api
    manager._bot_client = MagicMock()
    manager._bot_client.api = MagicMock()

    # 注册服务
    manager.register(PluginConfigService)
    manager.register(UnifiedRegistryService)
    manager.register(PluginDataService)

    # 加载服务
    await manager.load_all()

    # 修改数据目录
    manager.plugin_data._data_dir = temp_data_dir

    yield manager

    await manager.close_all()


@pytest_asyncio.fixture
async def plugin_loader(service_manager):
    """创建插件加载器"""
    event_bus = EventBus()
    loader = PluginLoader(
        event_bus=event_bus, service_manager=service_manager, debug=True
    )
    return loader


# =============================================================================
# 基础持久化测试
# =============================================================================


@pytest.mark.asyncio
async def test_plugin_data_initialized_on_load(plugin_loader):
    """测试插件加载时 data 被初始化"""
    plugin = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    assert hasattr(plugin, "data")
    assert isinstance(plugin.data, dict)
    assert plugin.data["loaded"] is True
    assert plugin.data["load_count"] == 1


@pytest.mark.asyncio
async def test_plugin_data_persisted_on_unload(plugin_loader, temp_data_dir):
    """测试插件卸载时数据被持久化"""
    plugin = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    plugin.data["test_value"] = "should_be_saved"

    await plugin.__unload__()

    # 验证数据文件存在
    data_file = temp_data_dir / "data_test_plugin.json"
    assert data_file.exists()

    # 验证数据内容
    with open(data_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["test_value"] == "should_be_saved"
    assert saved_data["closed"] is True


@pytest.mark.asyncio
async def test_plugin_data_restored_on_reload(plugin_loader, temp_data_dir):
    """测试插件重新加载时数据被恢复"""
    # 第一次加载
    plugin1 = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    plugin1.data["persistent_value"] = "this_should_persist"
    assert plugin1.data["load_count"] == 1

    await plugin1.__unload__()

    # 第二次加载
    plugin2 = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    # 验证数据被恢复
    assert plugin2.data["persistent_value"] == "this_should_persist"
    assert plugin2.data["load_count"] == 2  # 计数器应该增加


@pytest.mark.asyncio
async def test_multiple_load_unload_cycles(plugin_loader):
    """测试多次加载卸载循环"""
    for i in range(1, 4):
        plugin = await plugin_loader._load_plugin_by_class(
            DataPersistenceTestPlugin, "data_test_plugin"
        )

        assert plugin.data["load_count"] == i

        await plugin.__unload__()

        assert plugin.data["close_count"] == i


# =============================================================================
# 复杂数据结构测试
# =============================================================================


@pytest.mark.asyncio
async def test_complex_data_structures(plugin_loader, temp_data_dir):
    """测试复杂数据结构的持久化"""
    # 第一次加载
    plugin1 = await plugin_loader._load_plugin_by_class(
        ComplexDataPlugin, "complex_data_plugin"
    )

    assert len(plugin1.data["users"]) == 1
    assert plugin1.data["users"][0]["name"] == "user_1"

    await plugin1.__unload__()

    # 第二次加载
    plugin2 = await plugin_loader._load_plugin_by_class(
        ComplexDataPlugin, "complex_data_plugin"
    )

    # 验证数据累积
    assert len(plugin2.data["users"]) == 2
    assert plugin2.data["users"][1]["name"] == "user_2"
    assert len(plugin2.data["logs"]) == 2


@pytest.mark.asyncio
async def test_nested_data_persistence(plugin_loader, temp_data_dir):
    """测试嵌套数据的持久化"""
    plugin = await plugin_loader._load_plugin_by_class(
        ComplexDataPlugin, "complex_data_plugin"
    )

    # 创建深层嵌套结构
    plugin.data["deep"] = {
        "level1": {"level2": {"level3": {"value": "deep_value", "list": [1, 2, 3]}}}
    }

    await plugin.__unload__()

    # 重新加载并验证
    plugin2 = await plugin_loader._load_plugin_by_class(
        ComplexDataPlugin, "complex_data_plugin"
    )

    assert plugin2.data["deep"]["level1"]["level2"]["level3"]["value"] == "deep_value"
    assert plugin2.data["deep"]["level1"]["level2"]["level3"]["list"] == [1, 2, 3]


# =============================================================================
# 多插件测试
# =============================================================================


@pytest.mark.asyncio
async def test_multiple_plugins_independent_data(plugin_loader, temp_data_dir):
    """测试多个插件的数据独立性"""
    # 加载两个不同的插件
    plugin1 = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    plugin2 = await plugin_loader._load_plugin_by_class(
        ComplexDataPlugin, "complex_data_plugin"
    )

    # 修改各自的数据
    plugin1.data["plugin1_only"] = "value1"
    plugin2.data["plugin2_only"] = "value2"

    # 卸载插件
    await plugin1.__unload__()
    await plugin2.__unload__()

    # 验证两个数据文件都存在
    data_file1 = temp_data_dir / "data_test_plugin.json"
    data_file2 = temp_data_dir / "complex_data_plugin.json"

    assert data_file1.exists()
    assert data_file2.exists()

    # 验证数据独立
    with open(data_file1, "r", encoding="utf-8") as f:
        data1 = json.load(f)
    with open(data_file2, "r", encoding="utf-8") as f:
        data2 = json.load(f)

    assert "plugin1_only" in data1
    assert "plugin1_only" not in data2
    assert "plugin2_only" in data2
    assert "plugin2_only" not in data1


# =============================================================================
# 边界情况测试
# =============================================================================


@pytest.mark.asyncio
async def test_empty_data_on_first_load(plugin_loader):
    """测试首次加载时数据为空"""
    plugin = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "new_plugin"
    )

    # load_count 应该是 1（在 on_load 中设置）
    assert plugin.data.get("load_count") == 1
    # 但其他键不应该存在（除非在 on_load 中设置）
    assert "load_count" in plugin.data


@pytest.mark.asyncio
async def test_data_modification_between_load_and_unload(plugin_loader):
    """测试加载和卸载之间的数据修改"""
    plugin = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    # 在运行时修改数据
    plugin.data["runtime_value"] = "added_during_runtime"
    plugin.data["counter"] = 100

    await plugin.__unload__()

    # 重新加载并验证
    plugin2 = await plugin_loader._load_plugin_by_class(
        DataPersistenceTestPlugin, "data_test_plugin"
    )

    assert plugin2.data["runtime_value"] == "added_during_runtime"
    assert plugin2.data["counter"] == 100
