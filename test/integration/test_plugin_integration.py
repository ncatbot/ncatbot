"""
插件系统集成测试

测试插件的完整生命周期：加载、事件处理、卸载。
"""
import pytest
import asyncio
from typing import List, Any, Dict, Set
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import UUID

from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.client.ncatbot_event import NcatBotEvent
from ncatbot.plugin_system.pluginsys_err import PluginCircularDependencyError


# =============================================================================
# 模拟插件基类（简化版，避免导入问题）
# =============================================================================

class MockBasePlugin:
    """简化的测试插件基类"""
    
    name: str = None
    version: str = "1.0.0"
    author: str = "Test"
    description: str = "Test plugin"
    dependencies: Dict[str, str] = {}
    
    def __init__(self, event_bus: EventBus, **kwargs):
        if not self.name:
            raise ValueError("Plugin must have a name")
        self._event_bus = event_bus
        self._handlers_id: Set[UUID] = set()
        self.config: dict = {}
        self.workspace = kwargs.get("workspace", Path("/tmp"))
        
        # 生命周期追踪
        self._init_called = False
        self._load_called = False
        self._close_called = False
        self.events_received: List[NcatBotEvent] = []
    
    def _init_(self):
        """同步初始化"""
        self._init_called = True
    
    async def on_load(self):
        """异步加载"""
        self._load_called = True
    
    async def on_close(self):
        """异步关闭"""
        self._close_called = True
    
    def register_handler(self, event_type: str, handler, priority: int = 0) -> UUID:
        """注册事件处理器"""
        handler_id = self._event_bus.subscribe(event_type, handler, priority=priority)
        self._handlers_id.add(handler_id)
        return handler_id
    
    def unregister_all_handler(self):
        """注销所有处理器"""
        for hid in self._handlers_id:
            self._event_bus.unsubscribe(hid)
        self._handlers_id.clear()
    
    @property
    def meta_data(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
        }


# =============================================================================
# 测试插件
# =============================================================================

class GreeterPlugin(MockBasePlugin):
    """问候插件"""
    name = "greeter"
    version = "1.0.0"
    
    def __init__(self, event_bus, **kwargs):
        super().__init__(event_bus, **kwargs)
        self.greet_count = 0
    
    async def on_load(self):
        await super().on_load()
        # 注册消息处理器
        self.register_handler("ncatbot.message", self._on_message)
    
    def _on_message(self, event: NcatBotEvent):
        self.events_received.append(event)
        self.greet_count += 1


class LoggerPlugin(MockBasePlugin):
    """日志插件"""
    name = "logger"
    version = "2.0.0"
    
    def __init__(self, event_bus, **kwargs):
        super().__init__(event_bus, **kwargs)
        self.log_entries: List[str] = []
    
    async def on_load(self):
        await super().on_load()
        # 注册所有事件
        self.register_handler("re:ncatbot\\..*", self._log_event, priority=1000)
    
    def _log_event(self, event: NcatBotEvent):
        self.log_entries.append(f"[{event.type}] received")


class DependentPlugin(MockBasePlugin):
    """依赖其他插件的插件"""
    name = "dependent"
    version = "1.0.0"
    dependencies = {"greeter": ">=1.0.0"}


# =============================================================================
# 插件生命周期测试
# =============================================================================

class TestPluginLifecycle:
    """插件生命周期测试"""
    
    @pytest.mark.asyncio
    async def test_plugin_init_and_load(self, event_bus):
        """测试插件初始化和加载"""
        plugin = GreeterPlugin(event_bus)
        
        # 同步初始化
        plugin._init_()
        assert plugin._init_called
        
        # 异步加载
        await plugin.on_load()
        assert plugin._load_called
    
    @pytest.mark.asyncio
    async def test_plugin_close(self, event_bus):
        """测试插件关闭"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()
        
        # 关闭
        await plugin.on_close()
        assert plugin._close_called
    
    @pytest.mark.asyncio
    async def test_plugin_handler_unregistered_on_close(self, event_bus):
        """测试插件关闭时处理器被注销"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()
        
        # 验证有处理器
        assert len(plugin._handlers_id) > 0
        
        # 注销所有处理器
        plugin.unregister_all_handler()
        
        # 验证处理器被清空
        assert len(plugin._handlers_id) == 0


# =============================================================================
# 插件事件处理测试
# =============================================================================

class TestPluginEventHandling:
    """插件事件处理测试"""
    
    @pytest.mark.asyncio
    async def test_plugin_receives_events(self, event_bus):
        """测试插件接收事件"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()
        
        # 发布事件
        event = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event)
        
        assert plugin.greet_count == 1
        assert len(plugin.events_received) == 1
    
    @pytest.mark.asyncio
    async def test_multiple_plugins_handle_same_event(self, event_bus):
        """测试多个插件处理同一事件"""
        greeter = GreeterPlugin(event_bus)
        logger = LoggerPlugin(event_bus)
        
        greeter._init_()
        logger._init_()
        await greeter.on_load()
        await logger.on_load()
        
        # 发布消息事件
        event = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event)
        
        # 两个插件都应该收到
        assert greeter.greet_count == 1
        assert len(logger.log_entries) == 1
    
    @pytest.mark.asyncio
    async def test_plugin_priority_handling(self, event_bus):
        """测试插件优先级处理"""
        call_order = []
        
        class HighPriorityPlugin(MockBasePlugin):
            name = "high"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: call_order.append("high"), priority=100)
        
        class LowPriorityPlugin(MockBasePlugin):
            name = "low"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: call_order.append("low"), priority=1)
        
        high = HighPriorityPlugin(event_bus)
        low = LowPriorityPlugin(event_bus)
        
        await high.on_load()
        await low.on_load()
        
        event = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event)
        
        # 高优先级先执行
        assert call_order == ["high", "low"]
    
    @pytest.mark.asyncio
    async def test_unloaded_plugin_no_longer_receives_events(self, event_bus):
        """测试卸载后的插件不再接收事件"""
        plugin = GreeterPlugin(event_bus)
        plugin._init_()
        await plugin.on_load()
        
        # 第一次发布
        event1 = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event1)
        assert plugin.greet_count == 1
        
        # 卸载
        plugin.unregister_all_handler()
        
        # 第二次发布
        event2 = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event2)
        
        # 不应该再收到
        assert plugin.greet_count == 1


# =============================================================================
# 依赖解析测试
# =============================================================================

class TestDependencyResolution:
    """依赖解析测试"""
    
    def test_topological_sort_basic(self):
        """测试基本拓扑排序"""
        from ncatbot.plugin_system.loader.resolver import _DependencyResolver
        
        resolver = _DependencyResolver()
        
        # A 依赖 B，B 依赖 C
        manifests = {
            "A": {"dependencies": {"B": ">=1.0"}},
            "B": {"dependencies": {"C": ">=1.0"}},
            "C": {"dependencies": {}},
        }
        
        resolver.build(manifests)
        order = resolver.resolve()
        
        # C 必须在 B 之前，B 必须在 A 之前
        assert order.index("C") < order.index("B")
        assert order.index("B") < order.index("A")
    
    def test_circular_dependency_detection(self):
        """测试循环依赖检测"""
        from ncatbot.plugin_system.loader.resolver import _DependencyResolver
        
        resolver = _DependencyResolver()
        
        # A -> B -> C -> A (循环)
        manifests = {
            "A": {"dependencies": {"B": ">=1.0"}},
            "B": {"dependencies": {"C": ">=1.0"}},
            "C": {"dependencies": {"A": ">=1.0"}},
        }
        
        resolver.build(manifests)
        
        with pytest.raises(PluginCircularDependencyError):
            resolver.resolve()
    
    def test_independent_plugins_order(self):
        """测试独立插件可以任意顺序加载"""
        from ncatbot.plugin_system.loader.resolver import _DependencyResolver
        
        resolver = _DependencyResolver()
        
        manifests = {
            "A": {"dependencies": {}},
            "B": {"dependencies": {}},
            "C": {"dependencies": {}},
        }
        
        resolver.build(manifests)
        order = resolver.resolve()
        
        # 所有插件都应该在列表中
        assert set(order) == {"A", "B", "C"}
    
    def test_diamond_dependency(self):
        """测试菱形依赖"""
        from ncatbot.plugin_system.loader.resolver import _DependencyResolver
        
        resolver = _DependencyResolver()
        
        #     A
        #    / \
        #   B   C
        #    \ /
        #     D
        manifests = {
            "A": {"dependencies": {"B": ">=1.0", "C": ">=1.0"}},
            "B": {"dependencies": {"D": ">=1.0"}},
            "C": {"dependencies": {"D": ">=1.0"}},
            "D": {"dependencies": {}},
        }
        
        resolver.build(manifests)
        order = resolver.resolve()
        
        # D 必须在 B 和 C 之前
        assert order.index("D") < order.index("B")
        assert order.index("D") < order.index("C")
        # B 和 C 必须在 A 之前
        assert order.index("B") < order.index("A")
        assert order.index("C") < order.index("A")


# =============================================================================
# 插件配置测试
# =============================================================================

class TestPluginConfiguration:
    """插件配置测试"""
    
    @pytest.mark.asyncio
    async def test_plugin_config_default(self, event_bus):
        """测试插件默认配置"""
        plugin = GreeterPlugin(event_bus)
        
        assert plugin.config == {}
    
    @pytest.mark.asyncio
    async def test_plugin_metadata(self, event_bus):
        """测试插件元数据"""
        plugin = GreeterPlugin(event_bus)
        
        meta = plugin.meta_data
        assert meta["name"] == "greeter"
        assert meta["version"] == "1.0.0"


# =============================================================================
# 插件异常处理测试
# =============================================================================

class TestPluginExceptionHandling:
    """插件异常处理测试"""
    
    @pytest.mark.asyncio
    async def test_plugin_handler_exception_isolated(self, event_bus):
        """测试插件处理器异常被隔离"""
        results = []
        
        class BadPlugin(MockBasePlugin):
            name = "bad"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: (_ for _ in ()).throw(RuntimeError("Bad!")), priority=100)
        
        class GoodPlugin(MockBasePlugin):
            name = "good"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: results.append("good"), priority=1)
        
        bad = BadPlugin(event_bus)
        good = GoodPlugin(event_bus)
        
        await bad.on_load()
        await good.on_load()
        
        event = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event)
        
        # 好的插件仍然应该执行
        assert "good" in results
    
    @pytest.mark.asyncio
    async def test_plugin_must_have_name(self, event_bus):
        """测试插件必须有名称"""
        class NoNamePlugin(MockBasePlugin):
            pass  # 没有定义 name
        
        with pytest.raises(ValueError, match="must have a name"):
            NoNamePlugin(event_bus)


# =============================================================================
# 多插件协同测试
# =============================================================================

class TestMultiPluginCoordination:
    """多插件协同测试"""
    
    @pytest.mark.asyncio
    async def test_plugin_chain_processing(self, event_bus):
        """测试插件链式处理"""
        processing_chain = []
        
        class PreProcessor(MockBasePlugin):
            name = "pre"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: processing_chain.append("pre"), priority=100)
        
        class MainProcessor(MockBasePlugin):
            name = "main"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: processing_chain.append("main"), priority=50)
        
        class PostProcessor(MockBasePlugin):
            name = "post"
            async def on_load(self):
                self.register_handler("ncatbot.message", 
                    lambda e: processing_chain.append("post"), priority=1)
        
        pre = PreProcessor(event_bus)
        main = MainProcessor(event_bus)
        post = PostProcessor(event_bus)
        
        await pre.on_load()
        await main.on_load()
        await post.on_load()
        
        event = NcatBotEvent("ncatbot.message", MagicMock())
        await event_bus.publish(event)
        
        assert processing_chain == ["pre", "main", "post"]
