"""测试 BotAPI 注入到插件的功能"""

import pytest
import pytest_asyncio
from pathlib import Path

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.utils.testing import E2ETestSuite


class TestPluginAPIInjection:
    """测试插件 API 注入功能"""

    @pytest_asyncio.fixture
    async def test_suite(self):
        """创建测试套件"""
        suite = E2ETestSuite()
        await suite.setup()
        yield suite
        await suite.teardown()

    @pytest.mark.asyncio
    async def test_api_injected_to_plugin(self, test_suite: E2ETestSuite):
        """测试 BotAPI 被正确注入到插件实例中"""
        # 获取内置的 system_manager 插件
        plugins = test_suite.client.get_registered_plugins()
        assert len(plugins) > 0, "应该至少有一个内置插件被加载"

        # 验证每个插件都有 api 属性
        for plugin in plugins:
            assert hasattr(plugin, "api"), f"插件 {plugin.name} 应该有 api 属性"
            assert plugin.api is not None, f"插件 {plugin.name} 的 api 不应为 None"
            
            # 验证 api 是 BotAPI 的实例
            from ncatbot.core.api import BotAPI
            assert isinstance(
                plugin.api, BotAPI
            ), f"插件 {plugin.name} 的 api 应该是 BotAPI 的实例"

    @pytest.mark.asyncio
    async def test_api_same_as_client_api(self, test_suite: E2ETestSuite):
        """测试插件的 api 与 BotClient 的 api 是同一个实例"""
        plugins = test_suite.client.get_registered_plugins()
        assert len(plugins) > 0

        client_api = test_suite.client.api
        assert client_api is not None, "BotClient 的 api 不应为 None"

        for plugin in plugins:
            assert (
                plugin.api is client_api
            ), f"插件 {plugin.name} 的 api 应该与 BotClient 的 api 是同一个实例"

    @pytest.mark.asyncio
    async def test_plugin_can_use_api(self, test_suite: E2ETestSuite):
        """测试插件能够使用 api 调用方法"""
        plugins = test_suite.client.get_registered_plugins()
        assert len(plugins) > 0

        # 测试插件能访问 api 的方法
        plugin = plugins[0]
        
        # 验证 api 有常用的方法
        assert hasattr(plugin.api, "send_group_msg"), "api 应该有 send_group_msg 方法"
        assert hasattr(
            plugin.api, "send_private_msg"
        ), "api 应该有 send_private_msg 方法"
        assert hasattr(plugin.api, "get_login_info"), "api 应该有 get_login_info 方法"
        
        # 验证方法是可调用的
        assert callable(plugin.api.send_group_msg), "send_group_msg 应该是可调用的"
        assert callable(plugin.api.send_private_msg), "send_private_msg 应该是可调用的"
        assert callable(plugin.api.get_login_info), "get_login_info 应该是可调用的"
