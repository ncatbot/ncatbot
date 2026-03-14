"""Tests for ncatbot.utils.config.models - 数据模型层测试。"""

import os
import tempfile


from ncatbot.utils.config.models import (
    Config,
    NapCatConfig,
    PluginConfig,
    DEFAULT_BOT_UIN,
    DEFAULT_ROOT,
    DEFAULT_WS_TOKEN,
    DEFAULT_WEBUI_TOKEN,
)


class TestPluginConfig:
    """PluginConfig 测试。"""

    def test_default_values(self):
        """默认值测试。"""
        config = PluginConfig()
        assert config.plugins_dir == "plugins"
        assert config.plugin_whitelist == []
        assert config.plugin_blacklist == []
        assert config.load_plugin is False

    def test_custom_values(self):
        """自定义值测试。"""
        config = PluginConfig(
            plugins_dir="my_plugins",
            plugin_whitelist=["a", "b"],
            plugin_blacklist=["c"],
            load_plugin=False,
        )
        assert config.plugins_dir == "my_plugins"
        assert config.plugin_whitelist == ["a", "b"]
        assert config.plugin_blacklist == ["c"]
        assert config.load_plugin is False

    def test_empty_dir_defaults(self):
        """空目录默认为 plugins。"""
        config = PluginConfig(plugins_dir="")
        assert config.plugins_dir == "plugins"

    def test_ensure_dir_exists(self):
        """测试创建插件目录。"""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test_plugins")
            config = PluginConfig(plugins_dir=path)
            config.ensure_dir_exists()
            assert os.path.exists(path)


class TestNapCatConfig:
    """NapCatConfig 测试。"""

    def test_default_values(self):
        """默认值测试。"""
        config = NapCatConfig()
        assert config.ws_uri == "ws://localhost:3001"
        assert config.ws_token == DEFAULT_WS_TOKEN
        assert config.webui_uri == "http://localhost:6099"
        assert config.webui_token == DEFAULT_WEBUI_TOKEN
        assert config.enable_webui is True
        assert config.remote_mode is False

    def test_ws_uri_auto_scheme(self):
        """自动添加 ws:// 前缀。"""
        config = NapCatConfig(ws_uri="localhost:3001")
        assert config.ws_uri == "ws://localhost:3001"

    def test_webui_uri_auto_scheme(self):
        """自动添加 http:// 前缀。"""
        config = NapCatConfig(webui_uri="localhost:6099")
        assert config.webui_uri == "http://localhost:6099"

    def test_uri_parsing(self):
        """URI 解析测试。"""
        config = NapCatConfig(ws_uri="ws://192.168.1.1:3002")
        assert config.ws_host == "192.168.1.1"
        assert config.ws_port == 3002

    def test_get_security_issue_weak_default_token(self):
        """弱密码自动修复测试。"""
        config = NapCatConfig(ws_listen_ip="0.0.0.0", ws_token=DEFAULT_WS_TOKEN)
        issues = config.get_security_issues(auto_fix=True)
        assert len(issues) == 0
        assert config.ws_token != DEFAULT_WS_TOKEN  # 被自动修复

    def test_get_security_issue_custom_weak_token(self):
        """自定义弱密码不自动修复。"""
        config = NapCatConfig(ws_listen_ip="0.0.0.0", ws_token="weak")
        issues = config.get_security_issues(auto_fix=True)
        assert "WS 令牌强度不足" in issues

    def test_validate_assignment(self):
        """赋值触发校验。"""
        config = NapCatConfig()
        config.ws_uri = "192.168.1.1:3003"
        assert config.ws_uri == "ws://192.168.1.1:3003"


class TestConfig:
    """Config 主配置测试。"""

    def test_default_values(self):
        """默认值测试。"""
        config = Config()
        assert config.bot_uin == DEFAULT_BOT_UIN
        assert config.root == DEFAULT_ROOT
        assert config.debug is False
        assert config.websocket_timeout == 15

    def test_nested_configs(self):
        """嵌套配置测试。"""
        config = Config(
            napcat=NapCatConfig(ws_uri="ws://example.com:3001"),
            plugin=PluginConfig(plugins_dir="my_plugins"),
        )
        assert config.napcat.ws_uri == "ws://example.com:3001"
        assert config.plugin.plugins_dir == "my_plugins"

    def test_qq_number_coercion(self):
        """QQ 号强制转字符串。"""
        config = Config(bot_uin=123456789, root=987654321)
        assert config.bot_uin == "123456789"
        assert config.root == "987654321"

    def test_timeout_validation(self):
        """超时时间校验。"""
        config = Config(websocket_timeout=0)
        assert config.websocket_timeout >= 1

    def test_is_local(self):
        """本地服务判断。"""
        config = Config()
        assert config.is_local() is True

        config.napcat.ws_uri = "ws://192.168.1.1:3001"
        assert config.is_local() is False

    def test_is_default_uin(self):
        """默认 QQ 号判断。"""
        config = Config()
        assert config.is_default_uin() is True

        config.bot_uin = "999888777"
        assert config.is_default_uin() is False

    def test_model_validate_from_dict(self):
        """从字典创建配置。"""
        data = {
            "bot_uin": "123456789",
            "napcat": {"ws_uri": "ws://localhost:3001"},
            "plugin": {"plugins_dir": "my_plugins"},
        }
        config = Config.model_validate(data)
        assert config.bot_uin == "123456789"
        assert config.napcat.ws_uri == "ws://localhost:3001"
        assert config.plugin.plugins_dir == "my_plugins"

    def test_model_dump(self):
        """导出配置为字典。"""
        config = Config(bot_uin="123456789")
        data = config.model_dump()
        assert data["bot_uin"] == "123456789"
        assert "napcat" in data
        assert "plugin" in data
