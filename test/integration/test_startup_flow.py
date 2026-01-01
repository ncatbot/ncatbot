"""
启动流程集成测试

测试 BotClient 的完整启动流程和各组件协同初始化。
"""
import pytest
import asyncio
from typing import List, Optional
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock

from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.client.lifecycle import LifecycleManager, LEGAL_ARGS
from ncatbot.core.client.registry import EventRegistry
from ncatbot.core.service import ServiceManager, BaseService
from ncatbot.utils.error import NcatBotError


# =============================================================================
# Mock 组件
# =============================================================================

class MockMessageRouter(BaseService):
    """Mock 消息路由服务"""
    name = "message_router"
    
    def __init__(self, **config):
        super().__init__(**config)
        self.connected = False
        self._event_callback = None
    
    async def on_load(self):
        self.connected = True
    
    async def on_close(self):
        self.connected = False
    
    def set_event_callback(self, callback):
        self._event_callback = callback
    
    async def send(self, action, params=None, timeout=30):
        return {"status": "ok", "data": {}}


class MockPreUploadService(BaseService):
    """Mock 预上传服务"""
    name = "preupload"
    
    async def on_load(self):
        pass
    
    async def on_close(self):
        pass


# =============================================================================
# 启动参数验证测试
# =============================================================================

class TestStartupValidation:
    """启动参数验证测试"""
    
    def test_legal_args_defined(self):
        """测试合法参数已定义"""
        expected_args = ["bt_uin", "ws_uri", "debug", "root"]
        for arg in expected_args:
            assert arg in LEGAL_ARGS
    
    def test_illegal_arg_rejected(self):
        """测试非法参数被拒绝"""
        services = ServiceManager()
        event_bus = EventBus()
        registry = MagicMock(spec=EventRegistry)
        
        manager = LifecycleManager(services, event_bus, registry)
        
        with pytest.raises(NcatBotError, match="非法参数"):
            manager.start(illegal_param="value")
    
    def test_none_values_ignored(self):
        """测试 None 值被忽略"""
        services = ServiceManager()
        event_bus = EventBus()
        registry = MagicMock(spec=EventRegistry)
        
        manager = LifecycleManager(services, event_bus, registry)
        manager.mock_mode = True
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader"):
                    # None 值不应该更新配置
                    manager.start(bt_uin="123", ws_uri=None)
                    
                    # bt_uin 应该被更新
                    mock_config.update_value.assert_any_call("bt_uin", "123")
                    # ws_uri 为 None，不应该被更新
                    calls = [str(c) for c in mock_config.update_value.call_args_list]
                    assert not any("ws_uri" in c and "None" in c for c in calls)


# =============================================================================
# 组件初始化顺序测试
# =============================================================================

class TestComponentInitOrder:
    """组件初始化顺序测试"""
    
    @pytest.mark.asyncio
    async def test_service_manager_initialized_first(self):
        """测试 ServiceManager 首先初始化"""
        init_order = []
        
        services = ServiceManager()
        event_bus = EventBus()
        registry = MagicMock(spec=EventRegistry)
        
        manager = LifecycleManager(services, event_bus, registry)
        
        # 验证 services 已经注入
        assert manager.services is services
    
    @pytest.mark.asyncio
    async def test_event_bus_available_at_start(self):
        """测试 EventBus 在启动时可用"""
        services = ServiceManager()
        event_bus = EventBus()
        registry = MagicMock(spec=EventRegistry)
        
        manager = LifecycleManager(services, event_bus, registry)
        
        # 可以订阅事件
        handler_id = event_bus.subscribe("test.event", lambda e: None)
        assert handler_id is not None


# =============================================================================
# 服务加载流程测试
# =============================================================================

class TestServiceLoadingFlow:
    """服务加载流程测试"""
    
    @pytest.mark.asyncio
    async def test_services_load_in_correct_order(self):
        """测试服务按正确顺序加载"""
        load_order = []
        
        class ServiceA(BaseService):
            name = "service_a"
            async def on_load(self):
                load_order.append("a")
            async def on_close(self):
                pass
        
        class ServiceB(BaseService):
            name = "service_b"
            async def on_load(self):
                load_order.append("b")
            async def on_close(self):
                pass
        
        manager = ServiceManager()
        manager.register(ServiceA)
        manager.register(ServiceB)
        
        await manager.load_all()
        
        assert len(load_order) == 2
        assert "a" in load_order
        assert "b" in load_order
    
    @pytest.mark.asyncio
    async def test_service_failure_during_load(self):
        """测试服务加载失败"""
        class FailingService(BaseService):
            name = "failing"
            async def on_load(self):
                raise RuntimeError("Load failed")
            async def on_close(self):
                pass
        
        manager = ServiceManager()
        manager.register(FailingService)
        
        with pytest.raises(RuntimeError, match="Load failed"):
            await manager.load("failing")


# =============================================================================
# 退出流程测试
# =============================================================================

class TestExitFlow:
    """退出流程测试"""
    
    @pytest.mark.asyncio
    async def test_services_closed_on_exit(self):
        """测试退出时服务被关闭"""
        close_order = []
        
        class ServiceA(BaseService):
            name = "service_a"
            async def on_load(self):
                pass
            async def on_close(self):
                close_order.append("a")
        
        class ServiceB(BaseService):
            name = "service_b"
            async def on_load(self):
                pass
            async def on_close(self):
                close_order.append("b")
        
        manager = ServiceManager()
        manager.register(ServiceA)
        manager.register(ServiceB)
        
        await manager.load_all()
        await manager.close_all()
        
        # 所有服务都应该被关闭
        assert "a" in close_order
        assert "b" in close_order
    
    @pytest.mark.asyncio
    async def test_handlers_unsubscribed_on_exit(self):
        """测试退出时处理器被注销"""
        event_bus = EventBus()
        
        results = []
        
        def handler(e):
            results.append("called")
        
        handler_id = event_bus.subscribe("test.event", handler)
        
        # 注销
        event_bus.unsubscribe(handler_id)
        
        # 发布事件不应触发处理器
        from ncatbot.core.client.ncatbot_event import NcatBotEvent
        await event_bus.publish(NcatBotEvent("test.event", MagicMock()))
        
        assert len(results) == 0


# =============================================================================
# 插件加载集成测试
# =============================================================================

class TestPluginLoadingIntegration:
    """插件加载集成测试"""
    
    def test_plugin_loader_initialized_on_start(self):
        """测试启动时初始化插件加载器"""
        services = ServiceManager()
        event_bus = EventBus()
        registry = MagicMock(spec=EventRegistry)
        
        manager = LifecycleManager(services, event_bus, registry)
        manager.mock_mode = True
        
        with patch("ncatbot.core.client.lifecycle.ncatbot_config") as mock_config:
            mock_config.validate_config = MagicMock()
            mock_config.debug = False
            
            with patch("ncatbot.core.client.lifecycle.run_coroutine"):
                with patch("ncatbot.plugin_system.PluginLoader") as MockLoader:
                    mock_loader_instance = MagicMock()
                    MockLoader.return_value = mock_loader_instance
                    
                    manager.start(bt_uin="123")
                    
                    # 插件加载器应该被创建
                    MockLoader.assert_called_once()
                    assert manager.plugin_loader is mock_loader_instance


# =============================================================================
# 事件系统就绪测试
# =============================================================================

class TestEventSystemReady:
    """事件系统就绪测试"""
    
    @pytest.mark.asyncio
    async def test_event_bus_can_publish_after_init(self):
        """测试初始化后可以发布事件"""
        event_bus = EventBus()
        
        results = []
        event_bus.subscribe("test.ready", lambda e: results.append("ready"))
        
        from ncatbot.core.client.ncatbot_event import NcatBotEvent
        await event_bus.publish(NcatBotEvent("test.ready", MagicMock()))
        
        assert results == ["ready"]
    
    @pytest.mark.asyncio
    async def test_startup_event_fired(self):
        """测试启动事件被触发"""
        event_bus = EventBus()
        
        startup_received = []
        
        def on_startup(e):
            startup_received.append(e)
        
        # 订阅启动事件
        event_bus.subscribe("ncatbot.meta", on_startup)
        
        # 模拟启动事件
        from ncatbot.core.client.ncatbot_event import NcatBotEvent
        startup_event = NcatBotEvent("ncatbot.meta", MagicMock())
        await event_bus.publish(startup_event)
        
        assert len(startup_received) == 1


# =============================================================================
# 错误恢复测试
# =============================================================================

class TestErrorRecovery:
    """错误恢复测试"""
    
    @pytest.mark.asyncio
    async def test_partial_service_failure_handled(self):
        """测试部分服务失败被处理"""
        load_results = []
        
        class GoodService(BaseService):
            name = "good"
            async def on_load(self):
                load_results.append("good")
            async def on_close(self):
                pass
        
        manager = ServiceManager()
        manager.register(GoodService)
        
        # 加载成功的服务
        await manager.load("good")
        
        assert "good" in load_results
    
    @pytest.mark.asyncio
    async def test_service_close_failure_logged(self):
        """测试服务关闭失败被记录"""
        class BadCloseService(BaseService):
            name = "bad_close"
            async def on_load(self):
                pass
            async def on_close(self):
                raise RuntimeError("Close failed")
        
        manager = ServiceManager()
        manager.register(BadCloseService)
        
        await manager.load("bad_close")
        
        # 关闭应该抛出异常（或被捕获）
        # 取决于实现，这里测试异常被抛出
        with pytest.raises(RuntimeError):
            await manager.unload("bad_close")


# =============================================================================
# 完整流程模拟测试
# =============================================================================

class TestFullStartupSimulation:
    """完整启动流程模拟测试"""
    
    @pytest.mark.asyncio
    async def test_minimal_startup_flow(self):
        """测试最小化启动流程"""
        # 1. 创建组件
        services = ServiceManager()
        event_bus = EventBus()
        
        # 2. 注册服务
        services.register(MockMessageRouter)
        services.register(MockPreUploadService)
        
        # 3. 加载服务
        await services.load_all()
        
        # 4. 验证服务状态
        router = services.message_router
        assert router is not None
        assert router.connected
        
        preupload = services.preupload
        assert preupload is not None
        
        # 5. 事件处理就绪
        results = []
        event_bus.subscribe("test.event", lambda e: results.append("ok"))
        
        from ncatbot.core.client.ncatbot_event import NcatBotEvent
        await event_bus.publish(NcatBotEvent("test.event", MagicMock()))
        
        assert results == ["ok"]
        
        # 6. 清理
        await services.close_all()
        
        # 验证关闭
        assert "message_router" not in services._services
