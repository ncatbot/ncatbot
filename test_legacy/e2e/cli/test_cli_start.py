"""CLI start 命令端到端测试

使用 E2ETestSuite 测试 start 命令的启动和终止流程。
不使用任何 mock，通过真实的 MockServer 模拟 NapCat 服务。
"""

import asyncio

import pytest
import pytest_asyncio

from ncatbot.utils.testing import E2ETestSuite
from ncatbot.core import BotClient


class TestStartCommand:
    """start 命令端到端测试"""

    @pytest_asyncio.fixture
    async def test_suite(self):
        """创建测试套件"""
        suite = E2ETestSuite()
        await suite.setup()
        yield suite
        await suite.teardown()

    @pytest.mark.asyncio
    async def test_bot_client_starts_successfully(self, test_suite: E2ETestSuite):
        """测试 BotClient 成功启动"""
        # test_suite.setup() 已经启动了 BotClient
        client = test_suite.client

        # 验证客户端已正确初始化
        assert client is not None
        assert client.api is not None
        assert client.event_bus is not None
        assert client.services is not None

    @pytest.mark.asyncio
    async def test_bot_client_connects_to_server(self, test_suite: E2ETestSuite):
        """测试 BotClient 连接到服务器"""

        # 验证 MockServer 正在运行
        assert test_suite.mock_server is not None
        assert test_suite.mock_server.is_running

    @pytest.mark.asyncio
    async def test_bot_client_shutdown_gracefully(self, test_suite: E2ETestSuite):
        """测试 BotClient 优雅关闭"""
        client = test_suite.client

        # 验证客户端正在运行
        assert client is not None

        # 调用 shutdown 应该正常完成
        await client.shutdown()

        # 注意：teardown 会再次调用 shutdown，但应该是安全的


class TestStartWithPlugins:
    """带插件的 start 命令测试"""

    @pytest_asyncio.fixture
    async def test_suite(self):
        """创建测试套件"""
        suite = E2ETestSuite()
        await suite.setup()
        yield suite
        await suite.teardown()

    @pytest.mark.asyncio
    async def test_start_with_plugin_loader(self, test_suite: E2ETestSuite):
        """测试启动时插件加载器可用"""
        client = test_suite.client

        # 验证插件加载器已初始化
        assert hasattr(client, "plugin_loader")


class TestStartErrorHandling:
    """start 命令错误处理测试"""

    @pytest.mark.asyncio
    async def test_start_with_invalid_uri_fails(self):
        """测试连接无效 URI 时失败"""
        from ncatbot.utils import ncatbot_config

        # 保存原始配置
        original_uri = ncatbot_config.napcat.ws_uri

        try:
            # 设置无效的 URI
            ncatbot_config.napcat.ws_uri = "ws://localhost:99999"

            # 尝试创建客户端应该失败或超时
            BotClient.reset_singleton()
            client = BotClient()

            # run_backend_async 应该在连接失败时抛出异常
            with pytest.raises(Exception):
                await asyncio.wait_for(
                    client.run_backend_async(bot_uin="123456", mock=True),
                    timeout=3.0,
                )
        finally:
            # 恢复原始配置
            ncatbot_config.napcat.ws_uri = original_uri
            BotClient.reset_singleton()
