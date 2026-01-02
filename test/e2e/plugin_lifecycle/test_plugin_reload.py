"""
插件热重载端到端测试

测试插件的热重载功能：
- 重载流程（卸载 + 加载）
- 状态重置
- 配置值保持
- 命令重新注册
- 事件处理器重新注册

注意：每次加载都会创建新的插件模块和类，类变量会被重置。
"""

import pytest
import time

from .conftest import get_plugin_class


class TestBasicPluginReload:
    """基础插件重载测试"""

    def test_manual_reload_flow(self, test_suite, basic_plugin_name):
        """测试手动重载流程（卸载+加载）"""
        # 首次加载
        test_suite.register_plugin_sync(basic_plugin_name)
        BasicTestPlugin1 = get_plugin_class(basic_plugin_name)
        assert BasicTestPlugin1.load_count == 1
        assert BasicTestPlugin1.unload_count == 0

        # 模拟重载：先卸载
        test_suite.unregister_plugin_sync("basic_test_plugin")
        assert BasicTestPlugin1.unload_count == 1

        # 再次加载（会得到新的类）
        test_suite.register_plugin_sync(basic_plugin_name)
        BasicTestPlugin2 = get_plugin_class(basic_plugin_name)
        
        # 新类的 load_count 应该是 1（重置后）
        assert BasicTestPlugin2.load_count == 1
        assert BasicTestPlugin2.init_called is True

    def test_plugin_available_after_reload(self, test_suite, basic_plugin_name):
        """测试重载后插件仍然可用"""
        test_suite.register_plugin_sync(basic_plugin_name)
        test_suite.unregister_plugin_sync("basic_test_plugin")
        test_suite.register_plugin_sync(basic_plugin_name)

        plugin = test_suite.client.plugin_loader.get_plugin("basic_test_plugin")
        assert plugin is not None
        assert plugin.name == "basic_test_plugin"


class TestCommandReloadBehavior:
    """命令重载行为测试"""

    def test_commands_re_registered_after_reload(
        self, test_suite, command_plugin_name
    ):
        """测试重载后命令被重新注册"""
        test_suite.register_plugin_sync(command_plugin_name)

        # 验证命令存在且可执行
        test_suite.inject_group_message_sync("cmd_test")
        time.sleep(0.02)
        test_suite.assert_reply_sent()

        # 卸载并重新加载
        test_suite.clear_call_history()
        test_suite.unregister_plugin_sync("command_test_plugin")
        test_suite.register_plugin_sync(command_plugin_name)

        # 验证命令仍然可执行
        test_suite.inject_group_message_sync("cmd_test")
        time.sleep(0.02)
        test_suite.assert_reply_sent()

    def test_command_executable_after_reload(self, test_suite, command_plugin_name):
        """测试重载后命令可执行"""
        test_suite.register_plugin_sync(command_plugin_name)

        # 首次执行
        test_suite.inject_group_message_sync("cmd_test")
        time.sleep(0.02)
        test_suite.assert_reply_sent()

        # 重载
        test_suite.clear_call_history()
        test_suite.unregister_plugin_sync("command_test_plugin")
        test_suite.register_plugin_sync(command_plugin_name)

        # 重载后执行
        test_suite.inject_group_message_sync("cmd_test")
        time.sleep(0.02)
        test_suite.assert_reply_sent()

    def test_command_state_reset_after_reload(self, test_suite, command_plugin_name):
        """测试重载后命令状态被重置（类变量重置）"""
        test_suite.register_plugin_sync(command_plugin_name)
        CommandTestPlugin1 = get_plugin_class(command_plugin_name)

        # 执行命令，增加计数
        test_suite.inject_group_message_sync("cmd_test")
        time.sleep(0.02)
        assert len(CommandTestPlugin1.command_calls) >= 1

        # 重载
        test_suite.unregister_plugin_sync("command_test_plugin")
        test_suite.register_plugin_sync(command_plugin_name)
        CommandTestPlugin2 = get_plugin_class(command_plugin_name)

        # 验证新类的计数已重置
        assert len(CommandTestPlugin2.command_calls) == 0


class TestConfigReloadBehavior:
    """配置重载行为测试"""

    def test_config_values_preserved_after_reload(
        self, test_suite, config_plugin_name
    ):
        """测试重载后配置值被保持"""
        test_suite.register_plugin_sync(config_plugin_name)

        # 修改配置
        plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        plugin.set_config("api_key", "custom_key_before_reload")

        # 重载
        test_suite.unregister_plugin_sync("config_test_plugin")
        test_suite.register_plugin_sync(config_plugin_name)

        # 验证配置值被保持
        new_plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        assert new_plugin.config["api_key"] == "custom_key_before_reload"

    def test_config_registration_restored_after_reload(
        self, test_suite, config_plugin_name
    ):
        """测试重载后配置项注册被恢复"""
        test_suite.register_plugin_sync(config_plugin_name)

        # 卸载（配置注册被清理）
        test_suite.unregister_plugin_sync("config_test_plugin")
        config_service = test_suite.services.plugin_config
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 0

        # 重新加载（配置注册被恢复）
        test_suite.register_plugin_sync(config_plugin_name)
        configs = config_service.get_registered_configs("config_test_plugin")
        assert len(configs) == 3

    def test_new_config_merged_with_existing(self, test_suite, config_plugin_name):
        """测试新配置与现有配置合并"""
        test_suite.register_plugin_sync(config_plugin_name)

        # 修改一个配置
        plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        plugin.set_config("api_key", "modified_key")

        # 重载
        test_suite.unregister_plugin_sync("config_test_plugin")
        test_suite.register_plugin_sync(config_plugin_name)

        # 验证：修改的配置保持，未修改的使用默认值
        new_plugin = test_suite.client.plugin_loader.get_plugin("config_test_plugin")
        assert new_plugin.config["api_key"] == "modified_key"
        assert new_plugin.config["max_retries"] == 3  # 默认值


class TestHandlerReloadBehavior:
    """事件处理器重载行为测试"""

    def test_handlers_re_registered_after_reload(
        self, test_suite, handler_plugin_name
    ):
        """测试重载后事件处理器被重新注册（新ID）"""
        test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin1 = get_plugin_class(handler_plugin_name)
        first_handler_ids = set(HandlerTestPlugin1.handler_ids)
        assert len(first_handler_ids) == 2

        # 重载
        test_suite.unregister_plugin_sync("handler_test_plugin")
        test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin2 = get_plugin_class(handler_plugin_name)

        # 验证新的处理器被注册
        second_handler_ids = set(HandlerTestPlugin2.handler_ids)
        assert len(second_handler_ids) == 2

        # 新的处理器 ID 应该不同
        assert first_handler_ids != second_handler_ids

    def test_handler_receives_events_after_reload(
        self, test_suite, handler_plugin_name
    ):
        """测试重载后处理器能接收事件"""
        test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin1 = get_plugin_class(handler_plugin_name)

        # 发送消息
        test_suite.inject_group_message_sync("Before reload")
        time.sleep(0.02)
        events_before = len(HandlerTestPlugin1.message_events)
        assert events_before >= 1

        # 重载
        test_suite.unregister_plugin_sync("handler_test_plugin")
        test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin2 = get_plugin_class(handler_plugin_name)

        # 发送消息
        test_suite.inject_group_message_sync("After reload")
        time.sleep(0.02)

        # 应该收到新消息（新类的计数器从0开始）
        assert len(HandlerTestPlugin2.message_events) >= 1
        assert "After reload" in str(HandlerTestPlugin2.message_events)


class TestFullFeaturePluginReload:
    """完整功能插件重载测试"""

    def test_full_reload_lifecycle(self, test_suite, full_feature_plugin_name):
        """测试完整重载生命周期"""
        # 首次加载
        test_suite.register_plugin_sync(full_feature_plugin_name)
        FullFeaturePlugin1 = get_plugin_class(full_feature_plugin_name)
        assert "_init_" in FullFeaturePlugin1.lifecycle_events
        assert "on_load" in FullFeaturePlugin1.lifecycle_events
        assert len(FullFeaturePlugin1.lifecycle_events) == 2

        # 卸载
        test_suite.unregister_plugin_sync("full_feature_plugin")
        assert "on_close" in FullFeaturePlugin1.lifecycle_events
        assert len(FullFeaturePlugin1.lifecycle_events) == 3

        # 重新加载（得到新类）
        test_suite.register_plugin_sync(full_feature_plugin_name)
        FullFeaturePlugin2 = get_plugin_class(full_feature_plugin_name)

        # 验证新类的生命周期
        assert "_init_" in FullFeaturePlugin2.lifecycle_events
        assert "on_load" in FullFeaturePlugin2.lifecycle_events
        assert len(FullFeaturePlugin2.lifecycle_events) == 2

    def test_all_services_restored_after_reload(
        self, test_suite, full_feature_plugin_name
    ):
        """测试重载后所有服务被恢复"""
        test_suite.register_plugin_sync(full_feature_plugin_name)

        # 修改配置
        plugin = test_suite.client.plugin_loader.get_plugin("full_feature_plugin")
        plugin.set_config("feature_value", "before_reload")

        # 执行命令
        test_suite.inject_group_message_sync("ff_status")
        time.sleep(0.02)

        # 重载
        test_suite.clear_call_history()
        test_suite.unregister_plugin_sync("full_feature_plugin")
        test_suite.register_plugin_sync(full_feature_plugin_name)
        FullFeaturePlugin = get_plugin_class(full_feature_plugin_name)

        # 验证配置保持
        new_plugin = test_suite.client.plugin_loader.get_plugin("full_feature_plugin")
        assert new_plugin.config["feature_value"] == "before_reload"

        # 验证命令可用
        test_suite.inject_group_message_sync("ff_status")
        time.sleep(0.02)
        test_suite.assert_reply_sent()

        # 验证事件处理器工作
        assert len(FullFeaturePlugin.handler_events) >= 1


class TestRapidReload:
    """快速重载测试"""

    def test_multiple_rapid_reloads(self, test_suite, basic_plugin_name):
        """测试多次快速重载"""
        for i in range(3):
            test_suite.register_plugin_sync(basic_plugin_name)
            BasicTestPlugin = get_plugin_class(basic_plugin_name)
            assert BasicTestPlugin.load_count == 1  # 每次加载都是新类
            test_suite.unregister_plugin_sync("basic_test_plugin")
            assert BasicTestPlugin.unload_count == 1

        # 最终状态应该是卸载的
        plugin = test_suite.client.plugin_loader.get_plugin("basic_test_plugin")
        assert plugin is None

    def test_reload_with_pending_events(self, test_suite, handler_plugin_name):
        """测试有待处理事件时的重载"""
        test_suite.register_plugin_sync(handler_plugin_name)

        # 发送消息
        test_suite.inject_group_message_sync("Event 1")

        # 立即重载（不等待事件处理完成）
        test_suite.unregister_plugin_sync("handler_test_plugin")
        test_suite.register_plugin_sync(handler_plugin_name)
        HandlerTestPlugin = get_plugin_class(handler_plugin_name)

        # 发送新消息
        test_suite.inject_group_message_sync("Event 2")
        time.sleep(0.2)

        # 应该能收到新消息
        assert len(HandlerTestPlugin.message_events) >= 1
