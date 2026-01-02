"""
插件加载端到端测试

测试插件的加载流程和初始化：
- 基本加载流程
- 生命周期钩子调用
- 与各服务的协作初始化
"""

import pytest
import time

from .conftest import get_plugin_class


class TestBasicPluginLoading:
    """基础插件加载测试"""

    def test_plugin_loads_successfully(self, test_suite, basic_plugin_name):
        """测试插件能够成功加载"""
        plugin = test_suite.register_plugin_sync(basic_plugin_name)

        assert plugin is not None
        assert plugin.name == "basic_test_plugin"
        assert plugin.version == "1.0.0"

    def test_init_hook_called(self, test_suite, basic_plugin_name):
        """测试 _init_ 钩子被调用"""
        test_suite.register_plugin_sync(basic_plugin_name)
        BasicTestPlugin = get_plugin_class(basic_plugin_name)

        assert BasicTestPlugin.init_called is True

    def test_on_load_hook_called(self, test_suite, basic_plugin_name):
        """测试 on_load 钩子被调用"""
        test_suite.register_plugin_sync(basic_plugin_name)
        BasicTestPlugin = get_plugin_class(basic_plugin_name)

        assert BasicTestPlugin.load_count == 1

    def test_plugin_in_loader_registry(self, test_suite, basic_plugin_name):
        """测试插件被注册到加载器中"""
        test_suite.register_plugin_sync(basic_plugin_name)

        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" in plugins

    def test_plugin_can_be_retrieved(self, test_suite, basic_plugin_name):
        """测试可以通过名称获取插件"""
        test_suite.register_plugin_sync(basic_plugin_name)

        plugin = test_suite.client.plugin_loader.get_plugin("basic_test_plugin")
        assert plugin is not None
        assert plugin.name == "basic_test_plugin"


class TestPluginLoadingWithCommands:
    """带命令的插件加载测试"""

    def test_commands_registered_on_load(self, test_suite, command_plugin_name):
        """测试命令在加载时被注册"""
        test_suite.register_plugin_sync(command_plugin_name)

        # 检查 unified_registry 中的命令
        registry = test_suite.services.unified_registry
        registry.initialize_if_needed()

        commands = registry.command_registry.get_all_commands()
        command_names = [path[0] for path in commands.keys()]
        assert "cmd_test" in command_names

    def test_command_aliases_registered(self, test_suite, command_plugin_name):
        """测试命令别名被注册"""
        test_suite.register_plugin_sync(command_plugin_name)

        registry = test_suite.services.unified_registry
        registry.initialize_if_needed()

        aliases = registry.command_registry.get_all_aliases()
        alias_names = [path[0] for path in aliases.keys()]
        assert "ct" in alias_names

    def test_command_executable_after_load(self, test_suite, command_plugin_name):
        """测试加载后命令可执行"""
        test_suite.register_plugin_sync(command_plugin_name)

        test_suite.inject_group_message_sync("cmd_test")
        time.sleep(0.02)

        test_suite.assert_reply_sent("cmd_test executed")


class TestPluginLoadingWithConfig:
    """带配置的插件加载测试"""

    def test_configs_registered_on_load(self, test_suite, config_plugin_name):
        """测试配置在加载时被注册"""
        test_suite.register_plugin_sync(config_plugin_name)

        # 检查 PluginConfigService 中的配置
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("config_test_plugin")

        assert "api_key" in configs
        assert "max_retries" in configs
        assert "enabled" in configs

    def test_config_defaults_applied(self, test_suite, config_plugin_name):
        """测试配置默认值被应用"""
        test_suite.register_plugin_sync(config_plugin_name)
        ConfigTestPlugin = get_plugin_class(config_plugin_name)

        # 验证加载时记录的配置值
        assert ConfigTestPlugin.config_values_on_load["api_key"] == "default_api_key"
        assert ConfigTestPlugin.config_values_on_load["max_retries"] == 3
        assert ConfigTestPlugin.config_values_on_load["enabled"] in [True, "True", "true"]

    def test_config_accessible_via_plugin(self, test_suite, config_plugin_name):
        """测试配置可通过插件实例访问"""
        plugin = test_suite.register_plugin_sync(config_plugin_name)

        assert plugin.config["api_key"] == "default_api_key"
        assert plugin.config["max_retries"] == 3


class TestPluginLoadingWithHandlers:
    """带事件处理器的插件加载测试"""

    def test_handlers_registered_on_load(self, test_suite, handler_plugin_name):
        """测试事件处理器在加载时被注册"""
        plugin = test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 验证处理器 ID 被记录
        assert len(HandlerTestPlugin.handler_ids) == 2
        assert len(plugin._handlers_id) == 2

    def test_message_handler_receives_events(self, test_suite, handler_plugin_name):
        """测试消息处理器能接收事件"""
        test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        test_suite.inject_group_message_sync("Hello from test")
        time.sleep(0.02)

        assert len(HandlerTestPlugin.message_events) >= 1
        assert "Hello from test" in str(HandlerTestPlugin.message_events)


class TestFullFeaturePluginLoading:
    """完整功能插件加载测试"""

    def test_full_lifecycle_hooks(self, test_suite, full_feature_plugin_name):
        """测试完整生命周期钩子"""
        test_suite.register_plugin_sync(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        assert "_init_" in FullFeaturePlugin.lifecycle_events
        assert "on_load" in FullFeaturePlugin.lifecycle_events

    def test_all_services_initialized(self, test_suite, full_feature_plugin_name):
        """测试所有服务都被初始化"""
        plugin = test_suite.register_plugin_sync(full_feature_plugin_name)

        # 配置服务
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert "feature_enabled" in configs

        # 事件处理器
        assert len(plugin._handlers_id) == 2

        # unified_registry 命令
        registry = test_suite.services.unified_registry
        registry.initialize_if_needed()
        commands = registry.command_registry.get_all_commands()
        command_names = [path[0] for path in commands.keys()]
        assert "ff_status" in command_names

    def test_integrated_command_execution(self, test_suite, full_feature_plugin_name):
        """测试集成命令执行"""
        test_suite.register_plugin_sync(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        test_suite.inject_group_message_sync("ff_status")
        time.sleep(0.02)

        test_suite.assert_reply_sent()
        assert "ff_status" in FullFeaturePlugin.command_executions


class TestMultiplePluginLoading:
    """多插件加载测试"""

    def test_load_multiple_plugins(
        self, test_suite, basic_plugin_name, command_plugin_name
    ):
        """测试加载多个插件"""
        test_suite.register_plugin_sync(basic_plugin_name)
        test_suite.register_plugin_sync(command_plugin_name)

        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" in plugins
        assert "command_test_plugin" in plugins

    def test_plugins_dont_interfere(
        self, test_suite, handler_plugin_name, config_plugin_name
    ):
        """测试多插件之间不互相干扰"""
        test_suite.register_plugin_sync(handler_plugin_name)
        test_suite.register_plugin_sync(config_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)
        ConfigTestPlugin = get_plugin_class(config_plugin_name)

        # Handler 插件应该记录了消息事件处理器
        assert len(HandlerTestPlugin.handler_ids) == 2

        # Config 插件应该记录了配置
        assert len(ConfigTestPlugin.config_values_on_load) == 3

        # 两者应该独立
        config_service = test_suite.services.plugin_config
        handler_configs = config_service.get_registered_configs("handler_test_plugin")
        config_configs = config_service.get_registered_configs("config_test_plugin")

        # Handler 插件没有注册配置
        assert len(handler_configs) == 0
        # Config 插件有配置
        assert len(config_configs) == 3
