"""Tests for ncatbot.utils.config.manager - 管理层测试。"""

import os
import tempfile

import yaml

from ncatbot.utils.config.manager import ConfigManager, get_config_manager


class TestConfigManager:
    """ConfigManager 测试。"""

    def test_lazy_load(self):
        """懒加载测试。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w") as f:
                yaml.dump({"bot_uin": "999888777"}, f)

            manager = ConfigManager(path)
            assert manager._config is None
            _ = manager.config
            assert manager._config is not None

    def test_reload(self):
        """重新加载测试。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w") as f:
                yaml.dump({"bot_uin": "111"}, f)

            manager = ConfigManager(path)
            assert manager.bot_uin == "111"

            with open(path, "w") as f:
                yaml.dump({"bot_uin": "222"}, f)

            manager.reload()
            assert manager.bot_uin == "222"


class TestConfigManagerNapCat:
    """NapCat 配置访问测试。"""

    def test_ws_uri(self):
        """WS URI 读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.napcat.ws_uri == "ws://localhost:3001"

            manager.set_ws_uri("192.168.1.1:3002")
            assert manager.napcat.ws_uri == "ws://192.168.1.1:3002"

    def test_ws_token(self):
        """WS Token 读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            manager.set_ws_token("my_token")
            assert manager.napcat.ws_token == "my_token"

    def test_webui(self):
        """WebUI 配置读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.napcat.enable_webui is True

            manager.set_webui_enabled(False)
            assert manager.napcat.enable_webui is False

    def test_remote_mode(self):
        """远程模式读写（通过 napcat 属性访问）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.napcat.remote_mode is False

            manager.napcat.remote_mode = True
            assert manager.napcat.remote_mode is True


class TestConfigManagerPlugin:
    """插件配置访问测试。"""

    def test_plugins_dir(self):
        """插件目录读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.get_plugins_dir() == "plugins"

            manager.set_plugins_dir("my_plugins")
            assert manager.get_plugins_dir() == "my_plugins"

    def test_whitelist_blacklist(self):
        """白名单黑名单读写（通过 plugin 属性访问）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            manager.plugin.whitelist = ["a", "b"]
            manager.plugin.blacklist = ["c"]

            assert manager.plugin.whitelist == ["a", "b"]
            assert manager.plugin.blacklist == ["c"]


class TestConfigManagerMain:
    """主配置访问测试。"""

    def test_bot_uin(self):
        """机器人 QQ 号读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            manager.set_bot_uin(123456789)
            assert manager.bot_uin == "123456789"

    def test_root(self):
        """管理员 QQ 号读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            manager.set_root(987654321)
            assert manager.root == "987654321"

    def test_debug(self):
        """调试模式读写。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.debug is False

            manager.set_debug(True)
            assert manager.debug is True

    def test_websocket_timeout(self):
        """WebSocket 超时读写（通过 config 属性访问）。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            manager.config.websocket_timeout = 30
            assert manager.config.websocket_timeout == 30


class TestConfigManagerUtility:
    """工具方法测试。"""

    def test_is_local(self):
        """本地服务判断。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.is_local() is True

            manager.set_ws_uri("ws://192.168.1.1:3001")
            assert manager.is_local() is False

    def test_is_default_uin(self):
        """默认 QQ 号判断。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            assert manager.is_default_uin() is True

            manager.set_bot_uin("999888777")
            assert manager.is_default_uin() is False

    def test_get_security_issue(self):
        """安全校验。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            issues = manager.get_issues()
            assert isinstance(issues, list)


class TestConfigManagerSave:
    """保存测试。"""

    def test_save(self):
        """保存配置。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w") as f:
                yaml.dump({}, f)

            manager = ConfigManager(path)
            manager.set_bot_uin("999888777")
            manager.save()

            # 重新加载验证
            manager2 = ConfigManager(path)
            assert manager2.bot_uin == "999888777"


class TestGetConfigManager:
    """get_config_manager 测试。"""

    def test_singleton(self):
        """单例模式。"""
        import ncatbot.utils.config.manager as mgr

        mgr._default_manager = None

        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "config.yaml")
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump({}, f)

            m1 = get_config_manager(path)
            m2 = get_config_manager()
            assert m1 is m2

            mgr._default_manager = None
