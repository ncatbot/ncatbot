"""
插件数据持久化服务单元测试

测试 PluginDataService 的核心功能。
"""

import pytest
import pytest_asyncio
import tempfile
import json
from pathlib import Path

from ncatbot.core.service.builtin.plugin_data import PluginDataService


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_data_dir():
    """创建临时数据目录"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest_asyncio.fixture
async def data_service(temp_data_dir):
    """创建数据服务实例"""
    service = PluginDataService()
    service._data_dir = temp_data_dir
    await service.on_load()
    yield service
    await service.on_close()


# =============================================================================
# PluginDataService 基础功能测试
# =============================================================================


@pytest.mark.asyncio
async def test_service_initialization(temp_data_dir):
    """测试服务初始化"""
    service = PluginDataService()
    service._data_dir = temp_data_dir
    await service.on_load()

    assert service.name == "plugin_data"
    assert service._data_dir == temp_data_dir
    assert temp_data_dir.exists()

    await service.on_close()


@pytest.mark.asyncio
async def test_load_nonexistent_plugin_data(data_service):
    """测试加载不存在的插件数据"""
    data = await data_service.load_plugin_data("test_plugin")

    assert data == {}
    assert "test_plugin" in data_service._data_cache


@pytest.mark.asyncio
async def test_load_and_save_plugin_data(data_service, temp_data_dir):
    """测试加载和保存插件数据"""
    plugin_name = "test_plugin"

    # 加载空数据
    data = await data_service.load_plugin_data(plugin_name)
    assert data == {}

    # 修改数据
    data["counter"] = 42
    data["name"] = "测试"
    data["items"] = [1, 2, 3]

    # 保存数据
    success = await data_service.save_plugin_data(plugin_name)
    assert success is True

    # 验证文件存在
    data_file = temp_data_dir / f"{plugin_name}.json"
    assert data_file.exists()

    # 验证文件内容
    with open(data_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["counter"] == 42
    assert saved_data["name"] == "测试"
    assert saved_data["items"] == [1, 2, 3]


@pytest.mark.asyncio
async def test_load_existing_plugin_data(data_service, temp_data_dir):
    """测试加载已存在的插件数据"""
    plugin_name = "existing_plugin"
    data_file = temp_data_dir / f"{plugin_name}.json"

    # 创建数据文件
    test_data = {"counter": 100, "users": ["alice", "bob"], "config": {"enabled": True}}
    with open(data_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f)

    # 加载数据
    loaded_data = await data_service.load_plugin_data(plugin_name)

    assert loaded_data["counter"] == 100
    assert loaded_data["users"] == ["alice", "bob"]
    assert loaded_data["config"]["enabled"] is True


@pytest.mark.asyncio
async def test_get_plugin_data_from_cache(data_service):
    """测试从缓存获取插件数据"""
    plugin_name = "cached_plugin"

    # 加载数据
    data = await data_service.load_plugin_data(plugin_name)
    data["test"] = "value"

    # 从缓存获取
    cached_data = data_service.get_plugin_data(plugin_name)

    assert cached_data is data
    assert cached_data["test"] == "value"


@pytest.mark.asyncio
async def test_get_plugin_data_not_loaded(data_service):
    """测试获取未加载的插件数据"""
    data = data_service.get_plugin_data("not_loaded_plugin")

    assert data == {}


@pytest.mark.asyncio
async def test_clear_plugin_data(data_service, temp_data_dir):
    """测试清除插件数据"""
    plugin_name = "clear_test_plugin"

    # 加载并保存数据
    data = await data_service.load_plugin_data(plugin_name)
    data["test"] = "data"
    await data_service.save_plugin_data(plugin_name)

    data_file = temp_data_dir / f"{plugin_name}.json"
    assert data_file.exists()

    # 清除数据
    success = await data_service.clear_plugin_data(plugin_name)
    assert success is True
    assert not data_file.exists()
    assert plugin_name not in data_service._data_cache


@pytest.mark.asyncio
async def test_save_without_load(data_service):
    """测试未加载就保存（应该跳过）"""
    success = await data_service.save_plugin_data("not_loaded")
    assert success is True  # 跳过但返回成功


@pytest.mark.asyncio
async def test_multiple_plugins(data_service, temp_data_dir):
    """测试多个插件同时使用"""
    plugins = ["plugin1", "plugin2", "plugin3"]

    # 为每个插件加载和设置数据
    for i, plugin_name in enumerate(plugins):
        data = await data_service.load_plugin_data(plugin_name)
        data["id"] = i
        data["name"] = plugin_name
        await data_service.save_plugin_data(plugin_name)

    # 验证所有文件都存在
    for plugin_name in plugins:
        data_file = temp_data_dir / f"{plugin_name}.json"
        assert data_file.exists()

    # 验证数据独立性
    for i, plugin_name in enumerate(plugins):
        data = data_service.get_plugin_data(plugin_name)
        assert data["id"] == i
        assert data["name"] == plugin_name


# =============================================================================
# 错误处理测试
# =============================================================================


@pytest.mark.asyncio
async def test_load_corrupted_json(data_service, temp_data_dir):
    """测试加载损坏的 JSON 文件"""
    plugin_name = "corrupted_plugin"
    data_file = temp_data_dir / f"{plugin_name}.json"

    # 创建损坏的 JSON 文件
    with open(data_file, "w", encoding="utf-8") as f:
        f.write("{invalid json content")

    # 加载应该返回空字典并处理错误
    data = await data_service.load_plugin_data(plugin_name)
    assert data == {}


@pytest.mark.asyncio
async def test_load_empty_json_file(data_service, temp_data_dir):
    """测试加载空的 JSON 文件"""
    plugin_name = "empty_plugin"
    data_file = temp_data_dir / f"{plugin_name}.json"

    # 创建空文件
    data_file.touch()

    # 加载应该返回空字典
    data = await data_service.load_plugin_data(plugin_name)
    assert data == {}


@pytest.mark.asyncio
async def test_service_close_saves_all_data(data_service, temp_data_dir):
    """测试服务关闭时保存所有数据"""
    plugins = ["plugin_a", "plugin_b"]

    # 为每个插件设置数据
    for plugin_name in plugins:
        data = await data_service.load_plugin_data(plugin_name)
        data["saved_on_close"] = True

    # 关闭服务（应该保存所有数据）
    await data_service.on_close()

    # 验证所有文件都存在且包含正确数据
    for plugin_name in plugins:
        data_file = temp_data_dir / f"{plugin_name}.json"
        assert data_file.exists()

        with open(data_file, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert saved_data["saved_on_close"] is True


# =============================================================================
# 数据格式测试
# =============================================================================


@pytest.mark.asyncio
async def test_complex_data_structures(data_service, temp_data_dir):
    """测试复杂数据结构的持久化"""
    plugin_name = "complex_plugin"

    data = await data_service.load_plugin_data(plugin_name)

    # 设置复杂数据
    data["nested"] = {"level1": {"level2": {"value": "deep"}}}
    data["list_of_dicts"] = [{"id": 1, "name": "first"}, {"id": 2, "name": "second"}]
    data["mixed"] = [1, "string", True, None, {"key": "value"}]

    # 保存并重新加载
    await data_service.save_plugin_data(plugin_name)

    # 清除缓存
    data_service._data_cache.clear()

    # 重新加载
    reloaded = await data_service.load_plugin_data(plugin_name)

    assert reloaded["nested"]["level1"]["level2"]["value"] == "deep"
    assert len(reloaded["list_of_dicts"]) == 2
    assert reloaded["list_of_dicts"][0]["name"] == "first"
    assert reloaded["mixed"][4]["key"] == "value"


@pytest.mark.asyncio
async def test_unicode_data(data_service, temp_data_dir):
    """测试 Unicode 数据的持久化"""
    plugin_name = "unicode_plugin"

    data = await data_service.load_plugin_data(plugin_name)
    data["chinese"] = "你好世界"
    data["emoji"] = "🎉🎊"
    data["mixed"] = "Hello 世界 🌍"

    await data_service.save_plugin_data(plugin_name)

    # 清除缓存并重新加载
    data_service._data_cache.clear()
    reloaded = await data_service.load_plugin_data(plugin_name)

    assert reloaded["chinese"] == "你好世界"
    assert reloaded["emoji"] == "🎉🎊"
    assert reloaded["mixed"] == "Hello 世界 🌍"
