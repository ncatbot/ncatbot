"""
EventBus 订阅和生命周期测试
"""

import uuid
from unittest.mock import MagicMock

import pytest


class TestEventBusSubscription:
    """测试 EventBus 订阅管理"""

    def test_subscribe_exact_match(self, event_bus):
        async def handler(event):
            return None

        handler_id = event_bus.subscribe("test.event", handler)

        assert isinstance(handler_id, uuid.UUID)
        assert "test.event" in event_bus._exact
        assert len(event_bus._exact["test.event"]) == 1

    def test_subscribe_returns_unique_uuid(self, event_bus):
        async def handler1(event):
            return None

        async def handler2(event):
            return None

        id1 = event_bus.subscribe("test.event", handler1)
        id2 = event_bus.subscribe("test.event", handler2)

        assert id1 != id2

    def test_subscribe_with_priority(self, event_bus):
        async def handler1(event):
            return None

        async def handler2(event):
            return None

        event_bus.subscribe("test.event", handler1, priority=1)
        event_bus.subscribe("test.event", handler2, priority=10)

        handlers = event_bus._exact["test.event"]
        assert handlers[0][1] == 10
        assert handlers[1][1] == 1

    def test_subscribe_with_plugin_metadata(self, event_bus):
        async def handler(event):
            return None

        plugin = MagicMock()
        plugin.meta_data = {"name": "TestPlugin", "version": "1.0"}

        handler_id = event_bus.subscribe("test.event", handler, plugin=plugin)

        assert handler_id in event_bus._handler_meta
        assert event_bus._handler_meta[handler_id]["name"] == "TestPlugin"

    def test_subscribe_rejects_regex(self, event_bus):
        async def handler(event):
            return None

        with pytest.raises(ValueError, match="不再支持正则"):
            event_bus.subscribe("re:test\\..*", handler)

    def test_subscribe_rejects_sync_handler(self, event_bus):
        def handler(event):
            return None

        with pytest.raises(TypeError, match="仅支持异步事件处理器"):
            event_bus.subscribe("test.event", handler)


class TestEventBusUnsubscribe:
    """测试 EventBus 取消订阅"""

    def test_unsubscribe_by_uuid(self, event_bus):
        async def handler(event):
            return None

        handler_id = event_bus.subscribe("test.event", handler)
        result = event_bus.unsubscribe(handler_id)

        assert result is True
        assert "test.event" not in event_bus._exact

    def test_unsubscribe_nonexistent(self, event_bus):
        fake_id = uuid.uuid4()
        result = event_bus.unsubscribe(fake_id)
        assert result is False

    def test_unsubscribe_cleans_metadata(self, event_bus):
        async def handler(event):
            return None

        plugin = MagicMock()
        plugin.meta_data = {"name": "TestPlugin"}
        handler_id = event_bus.subscribe("test.event", handler, plugin=plugin)

        event_bus.unsubscribe(handler_id)

        assert handler_id not in event_bus._handler_meta


class TestEventBusCollectHandlers:
    """测试处理器收集"""

    def test_collect_exact_handlers(self, event_bus):
        async def handler(event):
            return None

        event_bus.subscribe("test.event", handler)
        handlers = event_bus._collect_handlers("test.event")
        assert len(handlers) == 1

    def test_collect_handlers_sorted_by_priority(self, event_bus):
        async def handler_low(event):
            return None

        async def handler_high(event):
            return None

        event_bus.subscribe("test.event", handler_low, priority=1)
        event_bus.subscribe("test.event", handler_high, priority=100)

        handlers = event_bus._collect_handlers("test.event")
        assert handlers[0][1] == 100
        assert handlers[1][1] == 1


class TestEventBusLifecycle:
    """测试 EventBus 生命周期"""

    def test_shutdown_clears_handlers(self, event_bus):
        async def handler(event):
            return None

        plugin = MagicMock()
        plugin.meta_data = {"name": "Test"}

        event_bus.subscribe("test.event", handler, plugin=plugin)

        assert len(event_bus._exact) > 0
        assert len(event_bus._handler_meta) > 0

        event_bus.shutdown()

        assert len(event_bus._exact) == 0
        assert len(event_bus._handler_meta) == 0
