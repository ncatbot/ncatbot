"""热重载测试插件"""

from ncatbot.plugin_system import NcatBotPlugin
from ncatbot.core.service.builtin.unified_registry import command_registry
from ncatbot.core import MessageEvent
from ncatbot.utils import get_log

LOG = get_log("ReloadTestPlugin")

# 命令响应内容（用于测试热重载后命令输出变化）
COMMAND_RESPONSE: str = "original_response"


class ReloadTestPlugin(NcatBotPlugin):
    """热重载测试插件"""

    name = "reload_test_plugin"
    version = "1.0.0"

    # 生命周期追踪（类变量）
    load_count: int = 0
    unload_count: int = 0
    
    # 用于验证重载的标记值
    MARKER_VALUE: str = "original"

    async def on_load(self):
        ReloadTestPlugin.load_count += 1
        LOG.info(f"ReloadTestPlugin on_load (count: {self.load_count}, marker: {self.MARKER_VALUE})")

    async def on_close(self):
        ReloadTestPlugin.unload_count += 1
        LOG.info(f"ReloadTestPlugin on_close (count: {self.unload_count})")

    @command_registry.command(name="reload_test_cmd", description="热重载测试命令")
    async def test_command(self, event: MessageEvent):
        """测试命令，返回当前的响应内容"""
        await event.reply(COMMAND_RESPONSE)

    @classmethod
    def reset_counters(cls):
        cls.load_count = 0
        cls.unload_count = 0

    @classmethod
    def get_marker(cls) -> str:
        return cls.MARKER_VALUE
