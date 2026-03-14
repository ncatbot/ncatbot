"""Tests for ncatbot.utils.config.storage - 存储层测试。"""

import os
import tempfile

import yaml

from ncatbot.utils.config.storage import ConfigStorage
from ncatbot.utils.config.models import Config, NapCatConfig, PluginConfig


class TestConfigStorage:
    """ConfigStorage 测试。"""

    def test_init_default_path(self):
        """默认路径初始化。"""
        from ncatbot.utils.config.storage import CONFIG_PATH

        storage = ConfigStorage()
        assert storage.path == CONFIG_PATH

    def test_init_custom_path(self):
        """自定义路径初始化。"""
        storage = ConfigStorage("/custom/config.yaml")
        assert storage.path == "/custom/config.yaml"

    def test_exists(self):
        """文件存在检查。"""
        with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
            path = f.name

        try:
            storage = ConfigStorage(path)
            assert storage.exists() is True
        finally:
            os.unlink(path)

        storage = ConfigStorage("/nonexistent.yaml")
        assert storage.exists() is False


class TestConfigStorageLoad:
    """ConfigStorage.load 测试。"""

    def test_load_valid_file(self):
        """加载有效文件。"""
        data = {"bot_uin": "123456789", "debug": True}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = f.name

        try:
            storage = ConfigStorage(path)
            config = storage.load()
            assert config.bot_uin == "123456789"
            assert config.debug is True
        finally:
            os.unlink(path)

    def test_load_nested_config(self):
        """加载嵌套配置。"""
        data = {
            "bot_uin": "123456789",
            "napcat": {"ws_uri": "ws://localhost:3001"},
            "plugin": {"plugins_dir": "my_plugins"},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(data, f)
            path = f.name

        try:
            storage = ConfigStorage(path)
            config = storage.load()
            assert config.napcat.ws_uri == "ws://localhost:3001"
            assert config.plugin.plugins_dir == "my_plugins"
        finally:
            os.unlink(path)

    def test_load_nonexistent_file(self):
        """加载不存在的文件返回默认配置。"""
        storage = ConfigStorage("/nonexistent/config.yaml")
        config = storage.load()
        assert config.bot_uin == "123456"  # 默认值

    def test_load_empty_file(self):
        """加载空文件返回默认配置。"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("")
            path = f.name

        try:
            storage = ConfigStorage(path)
            config = storage.load()
            assert config.bot_uin == "123456"  # 默认值
        finally:
            os.unlink(path)


class TestConfigStorageSave:
    """ConfigStorage.save 测试。"""

    def test_save_config(self):
        """保存配置。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            storage = ConfigStorage(path)

            config = Config(bot_uin="999888777", debug=True)
            storage.save(config)

            # 验证文件内容
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            assert data["bot_uin"] == "999888777"
            assert data["debug"] is True

    def test_save_excludes_computed_fields(self):
        """保存时排除计算字段。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            storage = ConfigStorage(path)

            config = Config()
            storage.save(config)

            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            # 计算字段不应被保存
            assert "ws_host" not in data.get("napcat", {})
            assert "ws_port" not in data.get("napcat", {})

    def test_save_creates_directory(self):
        """保存时创建目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "subdir", "config.yaml")
            storage = ConfigStorage(path)

            config = Config()
            storage.save(config)

            assert os.path.exists(path)

    def test_round_trip(self):
        """保存后加载一致性。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            storage = ConfigStorage(path)

            original = Config(
                bot_uin="999888777",
                debug=True,
                napcat=NapCatConfig(ws_uri="ws://example.com:3001"),
                plugin=PluginConfig(plugins_dir="my_plugins"),
            )
            storage.save(original)

            loaded = storage.load()
            assert loaded.bot_uin == original.bot_uin
            assert loaded.debug == original.debug
            assert loaded.napcat.ws_uri == original.napcat.ws_uri
            assert loaded.plugin.plugins_dir == original.plugin.plugins_dir
