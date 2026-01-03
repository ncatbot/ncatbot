"""基础命令端到端测试

测试：
- 简单命令执行
- 带参数命令
- 带选项命令
- 命令别名
"""

import pytest


class TestSimpleCommands:
    """简单命令测试"""

    @pytest.mark.asyncio
    async def test_hello_command(self, basic_command_suite):
        """测试简单问候命令"""
        await basic_command_suite.inject_private_message("/hello")
        basic_command_suite.assert_reply_sent("你好！我是机器人。")

    @pytest.mark.asyncio
    async def test_ping_command(self, basic_command_suite):
        """测试 ping 命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/ping")
        basic_command_suite.assert_reply_sent("pong!")

    @pytest.mark.asyncio
    async def test_command_in_group(self, basic_command_suite):
        """测试群聊中的命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_group_message("/hello")
        basic_command_suite.assert_reply_sent("你好！我是机器人。")


class TestParameterCommands:
    """带参数命令测试"""

    @pytest.mark.asyncio
    async def test_echo_command(self, basic_command_suite):
        """测试回显命令"""
        await basic_command_suite.inject_private_message("/echo 测试文本")
        basic_command_suite.assert_reply_sent("你说的是: 测试文本")

    @pytest.mark.asyncio
    async def test_add_command(self, basic_command_suite):
        """测试加法命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/add 10 20")
        basic_command_suite.assert_reply_sent("10 + 20 = 30")

    @pytest.mark.asyncio
    async def test_greet_with_default(self, basic_command_suite):
        """测试带默认参数的命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/greet 小明")
        basic_command_suite.assert_reply_sent("你好, 小明!")

    @pytest.mark.asyncio
    async def test_greet_with_custom(self, basic_command_suite):
        """测试自定义参数的命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/greet 小明 早上好")
        basic_command_suite.assert_reply_sent("早上好, 小明!")


class TestOptionCommands:
    """带选项命令测试"""

    @pytest.mark.asyncio
    async def test_deploy_basic(self, basic_command_suite):
        """测试基础部署命令"""
        await basic_command_suite.inject_private_message("/deploy myapp")
        basic_command_suite.assert_reply_sent("正在部署 myapp 到 dev 环境")

    @pytest.mark.asyncio
    async def test_deploy_with_env(self, basic_command_suite):
        """测试指定环境的部署命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/deploy myapp --env=prod")
        basic_command_suite.assert_reply_sent("正在部署 myapp 到 prod 环境")

    @pytest.mark.asyncio
    async def test_deploy_with_verbose(self, basic_command_suite):
        """测试详细模式的部署命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/deploy myapp -v")
        basic_command_suite.assert_reply_sent("详细信息: 开始部署流程...")

    @pytest.mark.asyncio
    async def test_deploy_with_force(self, basic_command_suite):
        """测试强制模式的部署命令"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/deploy myapp --force")
        basic_command_suite.assert_reply_sent("(强制模式)")


class TestAliasCommands:
    """命令别名测试"""

    @pytest.mark.asyncio
    async def test_status_main_command(self, basic_command_suite):
        """测试主命令"""
        await basic_command_suite.inject_private_message("/status")
        basic_command_suite.assert_reply_sent("机器人运行正常")

    @pytest.mark.asyncio
    async def test_status_alias_stat(self, basic_command_suite):
        """测试别名 stat"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/stat")
        basic_command_suite.assert_reply_sent("机器人运行正常")

    @pytest.mark.asyncio
    async def test_status_alias_st(self, basic_command_suite):
        """测试别名 st"""
        basic_command_suite.clear_call_history()
        await basic_command_suite.inject_private_message("/st")
        basic_command_suite.assert_reply_sent("机器人运行正常")
