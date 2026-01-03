"""
插件卸载端到端测试

测试插件的卸载流程和清理：
- 生命周期钩子调用
- 事件处理器清理
- 命令注销
- 配置项注册清理
"""

import pytest
import asyncio

from .conftest import get_plugin_class
from ncatbot.utils.testing import E2ETestSuite


class TestBasicPluginUnloading:
    """基础插件卸载测试"""

    @pytest.mark.asyncio
    async def test_plugin_unloads_successfully(self, test_suite: E2ETestSuite, basic_plugin_name):
        """测试插件能够成功卸载"""
        await test_suite.register_plugin(basic_plugin_name)

        # 验证加载
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" in plugins

        # 卸载
        await test_suite.unregister_plugin("basic_test_plugin")

        # 验证卸载
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "basic_test_plugin" not in plugins

    @pytest.mark.asyncio
    async def test_on_close_hook_called(self, test_suite: E2ETestSuite, basic_plugin_name):
        """测试 on_close 钩子被调用"""
        await test_suite.register_plugin(basic_plugin_name)
        BasicTestPlugin = get_plugin_class(basic_plugin_name)
        await test_suite.unregister_plugin("basic_test_plugin")

        assert BasicTestPlugin.unload_count == 1

    @pytest.mark.asyncio
    async def test_plugin_not_retrievable_after_unload(self, test_suite: E2ETestSuite, basic_plugin_name):
        """测试卸载后无法获取插件"""
        await test_suite.register_plugin(basic_plugin_name)
        await test_suite.unregister_plugin("basic_test_plugin")

        plugin = test_suite.client.plugin_loader.get_plugin("basic_test_plugin")
        assert plugin is None


class TestCommandCleanupOnUnload:
    """命令清理测试 - 端到端验证"""

    @pytest.mark.asyncio
    async def test_command_responds_while_loaded(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试加载时命令能正确响应"""
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)

        # 发送命令，应该收到回复
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_reply_sent("cmd_test executed")

        # 验证命令被调用
        assert "cmd_test" in CommandTestPlugin.command_calls

    @pytest.mark.asyncio
    async def test_alias_responds_while_loaded(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试加载时别名能正确响应"""
        await test_suite.register_plugin(command_plugin_name)

        # 通过别名发送命令，应该收到回复
        await test_suite.inject_group_message("ct")
        test_suite.assert_reply_sent("cmd_test executed")

    @pytest.mark.asyncio
    async def test_command_no_response_after_unload(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试卸载后命令不再响应"""
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)

        # 验证命令可执行
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_reply_sent()

        # 清空调用历史
        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 卸载插件
        await test_suite.unregister_plugin("command_test_plugin")

        # 再次发送命令，不应该收到回复
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_no_reply()

    @pytest.mark.asyncio
    async def test_alias_no_response_after_unload(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试卸载后别名不再响应"""
        await test_suite.register_plugin(command_plugin_name)

        # 验证别名可执行
        await test_suite.inject_group_message("ct")
        test_suite.assert_reply_sent()

        # 清空调用历史
        test_suite.clear_call_history()

        # 卸载插件
        await test_suite.unregister_plugin("command_test_plugin")

        # 再次通过别名发送命令，不应该收到回复
        await test_suite.inject_group_message("ct")
        test_suite.assert_no_reply()

    @pytest.mark.asyncio
    async def test_plugin_removed_from_registry_after_unload(
        self, test_suite: E2ETestSuite, command_plugin_name
    ):
        """测试卸载后插件从注册表移除"""
        await test_suite.register_plugin(command_plugin_name)
        await test_suite.unregister_plugin("command_test_plugin")

        # 验证插件已被移除
        plugin = test_suite.client.plugin_loader.get_plugin("command_test_plugin")
        assert plugin is None


class TestConfigCleanupOnUnload:
    """配置清理测试"""

    @pytest.mark.asyncio
    async def test_config_registration_cleared_on_unload(
        self, test_suite: E2ETestSuite, config_plugin_name
    ):
        """测试卸载时配置项注册被清理"""
        await test_suite.register_plugin(config_plugin_name)

        # 验证配置已注册
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 3

        # 卸载插件
        await test_suite.unregister_plugin("config_test_plugin")

        # 验证配置项注册被清理
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 0

    @pytest.mark.asyncio
    async def test_config_values_preserved_after_unload(self, test_suite: E2ETestSuite, config_plugin_name):
        """测试卸载后配置值被保留"""
        await test_suite.register_plugin(config_plugin_name)

        # 修改配置
        plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        plugin.set_config("api_key", "modified_key")

        # 卸载插件
        await test_suite.unregister_plugin("config_test_plugin")

        # 验证配置值仍然存在（虽然注册已清理）
        config_service = test_suite.services.plugin_config
        value = config_service.get("config_test_plugin", "api_key")
        assert value == "modified_key"


class TestHandlerCleanupOnUnload:
    """事件处理器清理测试"""

    @pytest.mark.asyncio
    async def test_handlers_unregistered_on_unload(self, test_suite: E2ETestSuite, handler_plugin_name):
        """测试卸载时事件处理器被注销"""
        plugin = await test_suite.register_plugin(handler_plugin_name)

        # 验证处理器已注册
        assert len(plugin._handlers_id) == 2

        # 卸载插件
        await test_suite.unregister_plugin("handler_test_plugin")

        # 注意：plugin 实例仍然存在，但已从加载器中移除
        # 验证加载器中没有该插件
        loaded = test_suite.client.plugin_loader.get_plugin("handler_test_plugin")
        assert loaded is None

    @pytest.mark.asyncio
    async def test_handler_not_triggered_after_unload(self, test_suite: E2ETestSuite, handler_plugin_name):
        """测试卸载后事件处理器不被触发"""
        await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 发送消息，应该被处理
        await test_suite.inject_group_message("Before unload")
        events_before = len(HandlerTestPlugin.message_events)
        assert events_before >= 1

        # 卸载插件
        await test_suite.unregister_plugin("handler_test_plugin")

        # 发送消息，不应该被处理
        await test_suite.inject_group_message("After unload")

        # 事件计数不应增加
        assert len(HandlerTestPlugin.message_events) == events_before


class TestFullFeaturePluginUnloading:
    """完整功能插件卸载测试 - 端到端验证"""

    @pytest.mark.asyncio
    async def test_all_cleanup_on_unload(self, test_suite: E2ETestSuite, full_feature_plugin_name):
        """测试卸载时所有资源被清理"""
        plugin = await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        # 验证所有资源已初始化
        assert len(plugin._handlers_id) == 2
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 2

        # 端到端验证：命令能正确响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()

        # 清空历史
        test_suite.clear_call_history()

        # 卸载
        await test_suite.unregister_plugin("full_feature_plugin")

        # 验证 on_close 被调用
        assert "on_close" in FullFeaturePlugin.lifecycle_events

        # 验证配置注册被清理
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 0

        # 验证插件已从加载器移除
        plugin = test_suite.client.plugin_loader.get_plugin("full_feature_plugin")
        assert plugin is None

    @pytest.mark.asyncio
    async def test_command_no_response_after_full_unload(
        self, test_suite: E2ETestSuite, full_feature_plugin_name
    ):
        """测试卸载后命令不再响应 - 端到端验证"""
        await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        # 验证命令能正确响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()

        # 清空历史
        test_suite.clear_call_history()
        FullFeaturePlugin.reset_counters()

        # 卸载
        await test_suite.unregister_plugin("full_feature_plugin")

        # 端到端验证：命令不再响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_no_reply()

    @pytest.mark.asyncio
    async def test_handler_no_trigger_after_full_unload(
        self, test_suite: E2ETestSuite, full_feature_plugin_name
    ):
        """测试卸载后事件处理器不再触发"""
        await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        # 发送消息触发处理器
        await test_suite.inject_group_message("test message for handler")
        events_before = len(FullFeaturePlugin.handler_events)

        # 卸载
        await test_suite.unregister_plugin("full_feature_plugin")

        # 发送消息，处理器不应该被触发
        await test_suite.inject_group_message("after unload message")

        # 验证事件计数没有增加
        assert len(FullFeaturePlugin.handler_events) == events_before


class TestMultiplePluginUnloading:
    """多插件卸载测试"""

    @pytest.mark.asyncio
    async def test_unload_one_doesnt_affect_others(
        self, test_suite: E2ETestSuite, command_plugin_name, config_plugin_name
    ):
        """测试卸载一个插件不影响其他插件"""
        await test_suite.register_plugin(command_plugin_name)
        await test_suite.register_plugin(config_plugin_name)

        # 卸载命令插件
        await test_suite.unregister_plugin("command_test_plugin")

        # 配置插件应该仍然存在
        config_plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        assert config_plugin is not None

        # 配置插件的配置应该仍然存在
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 3

    @pytest.mark.asyncio
    async def test_unload_all_plugins(
        self, test_suite: E2ETestSuite, basic_plugin_name, command_plugin_name, config_plugin_name
    ):
        """测试卸载所有插件"""
        await test_suite.register_plugin(basic_plugin_name)
        await test_suite.register_plugin(command_plugin_name)
        await test_suite.register_plugin(config_plugin_name)
        BasicTestPlugin = get_plugin_class(basic_plugin_name)

        # 逐个卸载
        await test_suite.unregister_plugin("basic_test_plugin")
        await test_suite.unregister_plugin("command_test_plugin")
        await test_suite.unregister_plugin("config_test_plugin")

        # 验证生命周期钩子被调用
        assert BasicTestPlugin.unload_count == 1
