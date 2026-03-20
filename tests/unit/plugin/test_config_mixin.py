"""
ConfigMixin 规范测试

规范:
  M-01: _mixin_load() 从 YAML 加载配置
  M-02: set_config() 立即持久化
  M-03: get_config(key, default) 返回默认值
  M-04: remove_config() 返回 bool
  M-05: update_config() 批量更新
  M-06: 配置文件不存在时优雅返回空字典
"""

import pytest
import yaml

from ncatbot.plugin.mixin.config_mixin import ConfigMixin


class FakePlugin(ConfigMixin):
    """最小配置 mixin 实例"""

    def __init__(self, workspace):
        self.name = "test_plugin"
        self.workspace = workspace
        self.config = {}


@pytest.fixture
def plugin(tmp_path):
    return FakePlugin(tmp_path)


# ---- M-01: _mixin_load 加载 YAML ----


def test_mixin_load_from_yaml(tmp_path):
    """M-01: 从 config.yaml 加载配置"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("api_key: abc123\ntimeout: 30\n", encoding="utf-8")

    p = FakePlugin(tmp_path)
    p._mixin_load()

    assert p.config == {"api_key": "abc123", "timeout": 30}


def test_mixin_load_missing_file(plugin):
    """M-06: 配置文件不存在 → 返回空字典"""
    plugin._mixin_load()
    assert plugin.config == {}


# ---- M-02: set_config 持久化 ----


def test_set_config_persists(plugin):
    """M-02: set_config() 写入后 YAML 文件包含新值"""
    plugin.config = {}
    plugin.set_config("key", "value")

    assert plugin.config["key"] == "value"

    # 验证文件已写入
    raw = yaml.safe_load(plugin._config_path.read_text(encoding="utf-8"))
    assert raw["key"] == "value"


# ---- M-03: get_config 默认值 ----


def test_get_config_existing(plugin):
    """M-03: 已有 key → 返回值"""
    plugin.config = {"existing": 42}
    assert plugin.get_config("existing") == 42


def test_get_config_default(plugin):
    """M-03: 不存在的 key → 返回 default"""
    plugin.config = {}
    assert plugin.get_config("missing", "fallback") == "fallback"


def test_get_config_none_default(plugin):
    """M-03: 不传 default → 返回 None"""
    plugin.config = {}
    assert plugin.get_config("missing") is None


# ---- M-04: remove_config ----


def test_remove_config_existing(plugin):
    """M-04: 移除存在的 key → True"""
    plugin.config = {"key": "value"}
    result = plugin.remove_config("key")
    assert result is True
    assert "key" not in plugin.config


def test_remove_config_missing(plugin):
    """M-04: 移除不存在的 key → False"""
    plugin.config = {}
    result = plugin.remove_config("nonexistent")
    assert result is False


# ---- M-05: update_config ----


def test_update_config(plugin):
    """M-05: update_config() 批量更新并持久化"""
    plugin.config = {"a": 1}
    plugin.update_config({"b": 2, "c": 3})

    assert plugin.config == {"a": 1, "b": 2, "c": 3}
    # 验证已持久化
    raw = yaml.safe_load(plugin._config_path.read_text(encoding="utf-8"))
    assert raw == {"a": 1, "b": 2, "c": 3}


# ---- M-06: 非字典内容优雅处理 ----


def test_load_non_dict_yaml(tmp_path):
    """M-06: YAML 内容不是字典时 → 返回空字典"""
    config_path = tmp_path / "config.yaml"
    config_path.write_text("- item1\n- item2\n", encoding="utf-8")

    p = FakePlugin(tmp_path)
    p._mixin_load()
    assert p.config == {}


# ---- Mixin unload 持久化 ----


def test_mixin_unload_saves(plugin):
    """_mixin_unload() 将当前 config 保存到 YAML"""
    plugin.config = {"saved": True}
    plugin._mixin_unload()

    raw = yaml.safe_load(plugin._config_path.read_text(encoding="utf-8"))
    assert raw == {"saved": True}


# ---- _apply_global_overrides 不因 name 缺失崩溃 ----


def test_apply_global_overrides_with_name(tmp_path):
    """_apply_global_overrides 在 name 已设置时不抛异常"""
    p = FakePlugin(tmp_path)
    # 应正常执行（get_config_manager 可能不可用，但 exception 应被捕获）
    p._apply_global_overrides()
    # 不崩溃即通过
