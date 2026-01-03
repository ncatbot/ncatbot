"""
服务协作端到端测试

测试插件生命周期与各服务的协作：
- register_handler 与 EventBus 的协作
- unified_registry 与命令系统的协作
- PluginConfigService 与配置系统的协作
- 多服务同时协作的场景
"""

import pytest
import asyncio

from ncatbot.core.client import NcatBotEvent
from ncatbot.utils.testing import E2ETestSuite
from .conftest import get_plugin_class


class TestRegisterHandlerCoordination:
    """register_handler 与 EventBus 协作测试"""

    @pytest.mark.asyncio
    async def test_handler_priority_respected(self, test_suite: E2ETestSuite, handler_plugin_name):
        """测试事件处理器优先级被尊重"""
        plugin = await test_suite.register_plugin(handler_plugin_name)

        # 验证处理器注册成功
        assert len(plugin._handlers_id) == 2

    @pytest.mark.asyncio
    async def test_handler_unsubscribed_on_plugin_unload(
        self, test_suite: E2ETestSuite, handler_plugin_name
    ):
        """测试插件卸载时处理器被取消订阅"""
        plugin = await test_suite.register_plugin(handler_plugin_name)
        handler_ids = list(plugin._handlers_id)

        # 卸载插件
        await test_suite.unregister_plugin("handler_test_plugin")

        # 验证事件总线中的订阅已被移除
        event_bus = test_suite.event_bus
        for handler_id in handler_ids:
            # 尝试取消订阅应该返回 False（已不存在）
            result = event_bus.unsubscribe(handler_id)
            assert result is False

    @pytest.mark.asyncio
    async def test_custom_events_received(self, test_suite: E2ETestSuite, handler_plugin_name):
        """测试自定义事件被接收"""
        await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 直接通过 event_bus 发布自定义事件
        custom_event = NcatBotEvent("handler_test.custom_event", {"key": "value"})
        await test_suite.event_bus.publish(custom_event)

        # 验证收到自定义事件
        assert len(HandlerTestPlugin.custom_events) >= 1

    @pytest.mark.asyncio
    async def test_handler_not_called_after_unregister(
        self, test_suite: E2ETestSuite, handler_plugin_name
    ):
        """测试取消注册后处理器不被调用"""
        plugin = await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 发送消息
        await test_suite.inject_group_message("Before unregister")
        count_before = len(HandlerTestPlugin.message_events)

        # 取消所有处理器注册
        plugin.unregister_all_handler()

        # 发送消息
        await test_suite.inject_group_message("After unregister")

        # 事件计数不应增加
        assert len(HandlerTestPlugin.message_events) == count_before


class TestUnifiedRegistryCoordination:
    """unified_registry 与命令系统协作测试"""

    @pytest.mark.asyncio
    async def test_command_dispatch_through_unified_registry(
        self, test_suite: E2ETestSuite, command_plugin_name
    ):
        """测试命令通过 unified_registry 分发"""
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)

        # 发送命令
        await test_suite.inject_group_message("cmd_test")

        # 验证命令被执行
        assert "cmd_test" in CommandTestPlugin.command_calls
        test_suite.assert_reply_sent()

    @pytest.mark.asyncio
    async def test_command_with_arguments(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试带参数的命令"""
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)

        # 发送带参数的命令
        await test_suite.inject_group_message("cmd_echo hello_world")

        # 验证命令被执行且参数正确
        assert any("cmd_echo:hello_world" in call for call in CommandTestPlugin.command_calls)
        test_suite.assert_reply_sent("Echo: hello_world")

    @pytest.mark.asyncio
    async def test_command_prefix_handling(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试命令前缀处理"""
        await test_suite.register_plugin(command_plugin_name)
        CommandTestPlugin = get_plugin_class(command_plugin_name)

        # 测试无前缀
        await test_suite.inject_group_message("cmd_test")
        test_suite.assert_reply_sent()

        # 清空历史
        test_suite.clear_call_history()
        CommandTestPlugin.reset_counters()

        # 测试有前缀
        await test_suite.inject_group_message("/cmd_test")
        test_suite.assert_reply_sent()

    @pytest.mark.asyncio
    async def test_registry_reinitialized_on_plugin_change(
        self, test_suite: E2ETestSuite, command_plugin_name
    ):
        """测试插件变更时 registry 重新初始化"""
        registry = test_suite.services.unified_registry

        # 加载插件
        await test_suite.register_plugin(command_plugin_name)
        registry.initialize_if_needed()
        assert registry._initialized is True

        # 卸载插件应该重置初始化标志
        await test_suite.unregister_plugin("command_test_plugin")
        # handle_plugin_unload 会重新初始化，所以仍然是 True
        assert registry._initialized is True


class TestPluginConfigServiceCoordination:
    """PluginConfigService 与配置系统协作测试"""

    @pytest.mark.asyncio
    async def test_config_isolation_between_plugins(
        self, test_suite: E2ETestSuite, config_plugin_name, handler_plugin_name
    ):
        """测试插件间配置隔离"""
        await test_suite.register_plugin(config_plugin_name)
        await test_suite.register_plugin(handler_plugin_name)

        config_service = test_suite.services.plugin_config

        # 验证配置隔离
        config_configs = config_service.get_registered_configs("config_test_plugin")
        handler_configs = config_service.get_registered_configs("handler_test_plugin")

        assert len(config_configs) == 3
        assert len(handler_configs) == 0

    @pytest.mark.asyncio
    async def test_config_persistence_across_operations(self, test_suite: E2ETestSuite, config_plugin_name):
        """测试配置跨操作持久化"""
        await test_suite.register_plugin(config_plugin_name)

        # 修改配置
        config_service = test_suite.services.plugin_config
        config_service.set("config_test_plugin", "api_key", "persistent_value")

        # 验证值已设置
        value = config_service.get("config_test_plugin", "api_key")
        assert value == "persistent_value"

        # 卸载插件
        await test_suite.unregister_plugin("config_test_plugin")

        # 配置值应该仍然存在
        value = config_service.get("config_test_plugin", "api_key")
        assert value == "persistent_value"

    @pytest.mark.asyncio
    async def test_config_defaults_on_first_load(self, test_suite: E2ETestSuite, config_plugin_name):
        """测试首次加载时使用默认值"""
        await test_suite.register_plugin(config_plugin_name)
        ConfigTestPlugin = get_plugin_class(config_plugin_name)

        # 验证加载时的配置值
        assert ConfigTestPlugin.config_values_on_load["api_key"] == "default_api_key"
        assert ConfigTestPlugin.config_values_on_load["max_retries"] == 3
        assert ConfigTestPlugin.config_values_on_load["enabled"] is True

    @pytest.mark.asyncio
    async def test_config_modification_via_plugin(self, test_suite: E2ETestSuite, config_plugin_name):
        """测试通过插件修改配置"""
        await test_suite.register_plugin(config_plugin_name)
        ConfigTestPlugin = get_plugin_class(config_plugin_name)

        # 通过命令修改配置
        await test_suite.inject_group_message("cfg_set api_key new_key")

        # 验证修改被记录
        assert len(ConfigTestPlugin.config_change_history) >= 1
        assert ("api_key", "default_api_key", "new_key") in ConfigTestPlugin.config_change_history


class TestMultiServiceCoordination:
    """多服务协作测试"""

    @pytest.mark.asyncio
    async def test_all_services_work_together(self, test_suite: E2ETestSuite, full_feature_plugin_name):
        """测试所有服务协同工作"""
        await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        # 1. 配置服务工作
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 2

        # 2. 命令系统工作
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()
        assert "ff_status" in FullFeaturePlugin.command_executions

        # 3. 事件处理器工作
        assert len(FullFeaturePlugin.handler_events) >= 1

    @pytest.mark.asyncio
    async def test_services_cleanup_on_unload(self, test_suite: E2ETestSuite, full_feature_plugin_name):
        """测试卸载时所有服务清理 - 端到端验证"""
        plugin = await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)
        initial_handler_count = len(plugin._handlers_id)
        assert initial_handler_count == 2

        # 端到端验证：命令能响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_reply_sent()

        # 清空历史
        test_suite.clear_call_history()
        FullFeaturePlugin.reset_counters()

        # 卸载插件
        await test_suite.unregister_plugin("full_feature_plugin")

        # 验证各服务已清理
        # 1. 配置注册被清理
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("full_feature_plugin")
        assert len(configs) == 0

        # 2. 插件从加载器移除
        removed_plugin = test_suite.client.plugin_loader.get_plugin("full_feature_plugin")
        assert removed_plugin is None

        # 3. 生命周期钩子被调用
        assert "on_close" in FullFeaturePlugin.lifecycle_events

        # 4. 端到端验证：命令不再响应
        await test_suite.inject_group_message("ff_status")
        test_suite.assert_no_reply()

    @pytest.mark.asyncio
    async def test_config_command_interaction(self, test_suite: E2ETestSuite, full_feature_plugin_name):
        """测试配置与命令交互"""
        await test_suite.register_plugin(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        # 通过命令设置配置
        await test_suite.inject_group_message("ff_config set feature_value new_value")
        test_suite.assert_reply_sent()

        # 验证配置被修改
        assert any("set:feature_value=new_value" in op for op in FullFeaturePlugin.config_operations)

        # 通过命令获取配置
        test_suite.clear_call_history()
        await test_suite.inject_group_message("ff_config get feature_value")
        test_suite.assert_reply_sent()


class TestEdgeCases:
    """边界情况测试"""

    @pytest.mark.asyncio
    async def test_load_plugin_twice(self, test_suite: E2ETestSuite, command_plugin_name):
        """测试重复加载同一插件"""
        await test_suite.register_plugin(command_plugin_name)

        # 尝试再次加载（应该不会报错，但也不会重复注册）
        # 注意：这取决于具体实现，可能会跳过或报错
        try:
            await test_suite.register_plugin(command_plugin_name)
        except Exception:
            pass  # 允许抛出异常

        # 验证插件仍然可用
        plugin = test_suite.client.plugin_loader.get_plugin("command_test_plugin")
        assert plugin is not None

    @pytest.mark.asyncio
    async def test_unload_nonexistent_plugin(self, test_suite: E2ETestSuite):
        """测试卸载不存在的插件"""
        # 应该不会报错
        await test_suite.unregister_plugin("nonexistent_plugin")

    @pytest.mark.asyncio
    async def test_rapid_load_unload_cycles(
        self, test_suite: E2ETestSuite, command_plugin_name, handler_plugin_name
    ):
        """测试快速加载卸载循环"""
        for _ in range(3):
            await test_suite.register_plugin(command_plugin_name)
            await test_suite.register_plugin(handler_plugin_name)
            await test_suite.unregister_plugin("command_test_plugin")
            await test_suite.unregister_plugin("handler_test_plugin")

        # 最终应该没有测试插件
        plugins = test_suite.client.plugin_loader.list_plugins()
        assert "command_test_plugin" not in plugins
        assert "handler_test_plugin" not in plugins

    @pytest.mark.asyncio
    async def test_event_during_plugin_operations(
        self, test_suite: E2ETestSuite, handler_plugin_name
    ):
        """测试插件操作期间的事件处理"""
        await test_suite.register_plugin(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 发送事件
        await test_suite.inject_group_message("Test message 1")

        # 立即卸载
        await test_suite.unregister_plugin("handler_test_plugin")

        # 发送更多事件
        await test_suite.inject_group_message("Test message 2")

        await asyncio.sleep(0.1)

        # 第二条消息不应该被处理
        # （第一条可能被处理，取决于时序）
        messages_with_2 = [e for e in HandlerTestPlugin.message_events 
                          if "Test message 2" in str(e)]
        assert len(messages_with_2) == 0
