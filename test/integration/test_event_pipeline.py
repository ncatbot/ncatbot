"""
事件处理流水线集成测试

测试从原始 WebSocket 消息到事件处理器的完整流程：
WebSocket 数据 → EventDispatcher → EventBus → Handler

注意：事件类型格式为 ncatbot.{EventType.value}，即：
- ncatbot.message_event (消息事件)
- ncatbot.message_sent_event (消息发送事件)
- ncatbot.notice_event (通知事件)
- ncatbot.request_event (请求事件)
- ncatbot.meta_event (元事件)
"""
import pytest
import asyncio
from typing import List, Any
from unittest.mock import MagicMock, AsyncMock

from ncatbot.core.client.event_bus import EventBus
from ncatbot.core.client.dispatcher import EventDispatcher
from ncatbot.core.client.ncatbot_event import NcatBotEvent
from ncatbot.core.event.enums import EventType


# 事件类型常量
MESSAGE_EVENT = f"ncatbot.{EventType.MESSAGE.value}"            # ncatbot.message_event
MESSAGE_SENT_EVENT = f"ncatbot.{EventType.MESSAGE_SENT.value}"  # ncatbot.message_sent_event
NOTICE_EVENT = f"ncatbot.{EventType.NOTICE.value}"              # ncatbot.notice_event
REQUEST_EVENT = f"ncatbot.{EventType.REQUEST.value}"            # ncatbot.request_event
META_EVENT = f"ncatbot.{EventType.META.value}"                  # ncatbot.meta_event


# =============================================================================
# 事件处理流水线基础测试
# =============================================================================

class TestEventPipelineBasic:
    """事件处理流水线基础测试"""
    
    @pytest.mark.asyncio
    async def test_message_event_full_pipeline(self, event_bus, mock_api, sample_message_event):
        """测试消息事件完整流水线"""
        received_events: List[NcatBotEvent] = []
        
        def handler(event: NcatBotEvent):
            received_events.append(event)
        
        # 订阅消息事件
        event_bus.subscribe(MESSAGE_EVENT, handler)
        
        # 创建分发器并分发事件
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        # 验证处理器被调用
        assert len(received_events) == 1
        event = received_events[0]
        assert event.type == MESSAGE_EVENT
        assert event.data.group_id == "701784439"
        assert event.data.raw_message == "Hello"
    
    @pytest.mark.asyncio
    async def test_private_message_pipeline(self, event_bus, mock_api, sample_private_message_event):
        """测试私聊消息流水线"""
        received = []
        
        event_bus.subscribe(MESSAGE_EVENT, lambda e: received.append(e))
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_private_message_event)
        
        assert len(received) == 1
        assert received[0].data.user_id == "3051561876"
        assert received[0].data.message_type == "private"
    
    @pytest.mark.asyncio
    async def test_notice_event_pipeline(self, event_bus, mock_api, sample_notice_event):
        """测试通知事件流水线"""
        received = []
        
        event_bus.subscribe(NOTICE_EVENT, lambda e: received.append(e))
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_notice_event)
        
        assert len(received) == 1
        assert received[0].data.notice_type == "group_increase"
    
    @pytest.mark.asyncio
    async def test_request_event_pipeline(self, event_bus, mock_api, sample_request_event):
        """测试请求事件流水线"""
        received = []
        
        event_bus.subscribe(REQUEST_EVENT, lambda e: received.append(e))
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_request_event)
        
        assert len(received) == 1
        assert received[0].data.request_type == "friend"
    
    @pytest.mark.asyncio
    async def test_meta_event_pipeline(self, event_bus, mock_api, sample_meta_event):
        """测试元事件流水线"""
        received = []
        
        event_bus.subscribe(META_EVENT, lambda e: received.append(e))
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_meta_event)
        
        assert len(received) == 1


# =============================================================================
# 多处理器测试
# =============================================================================

class TestMultipleHandlers:
    """多处理器场景测试"""
    
    @pytest.mark.asyncio
    async def test_multiple_handlers_all_called(self, event_bus, mock_api, sample_message_event):
        """测试多个处理器都被调用"""
        call_order = []
        
        def handler1(e):
            call_order.append("handler1")
        
        def handler2(e):
            call_order.append("handler2")
        
        def handler3(e):
            call_order.append("handler3")
        
        event_bus.subscribe(MESSAGE_EVENT, handler1)
        event_bus.subscribe(MESSAGE_EVENT, handler2)
        event_bus.subscribe(MESSAGE_EVENT, handler3)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        assert len(call_order) == 3
        assert "handler1" in call_order
        assert "handler2" in call_order
        assert "handler3" in call_order
    
    @pytest.mark.asyncio
    async def test_handler_priority_order(self, event_bus, mock_api, sample_message_event):
        """测试处理器按优先级执行"""
        call_order = []
        
        def low_priority(e):
            call_order.append("low")
        
        def high_priority(e):
            call_order.append("high")
        
        def medium_priority(e):
            call_order.append("medium")
        
        # 不同优先级注册
        event_bus.subscribe(MESSAGE_EVENT, low_priority, priority=1)
        event_bus.subscribe(MESSAGE_EVENT, high_priority, priority=100)
        event_bus.subscribe(MESSAGE_EVENT, medium_priority, priority=50)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        # 高优先级先执行
        assert call_order[0] == "high"
        assert call_order[1] == "medium"
        assert call_order[2] == "low"
    
    @pytest.mark.asyncio
    async def test_async_handlers(self, event_bus, mock_api, sample_message_event):
        """测试异步处理器"""
        results = []
        
        async def async_handler(e):
            await asyncio.sleep(0.01)
            results.append("async_done")
        
        event_bus.subscribe(MESSAGE_EVENT, async_handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        assert results == ["async_done"]


# =============================================================================
# 异常处理测试
# =============================================================================

class TestHandlerExceptions:
    """处理器异常场景测试"""
    
    @pytest.mark.asyncio
    async def test_exception_does_not_stop_other_handlers(self, event_bus, mock_api, sample_message_event):
        """测试一个处理器异常不影响其他处理器"""
        results = []
        
        def good_handler1(e):
            results.append("good1")
        
        def bad_handler(e):
            raise ValueError("Handler error")
        
        def good_handler2(e):
            results.append("good2")
        
        # 高优先级的好处理器
        event_bus.subscribe(MESSAGE_EVENT, good_handler1, priority=100)
        # 中等优先级的坏处理器
        event_bus.subscribe(MESSAGE_EVENT, bad_handler, priority=50)
        # 低优先级的好处理器
        event_bus.subscribe(MESSAGE_EVENT, good_handler2, priority=1)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        # 两个好处理器都应该执行
        assert "good1" in results
        assert "good2" in results
    
    @pytest.mark.asyncio
    async def test_async_exception_handling(self, event_bus, mock_api, sample_message_event):
        """测试异步处理器异常"""
        results = []
        
        async def async_bad(e):
            raise RuntimeError("Async error")
        
        async def async_good(e):
            results.append("async_good")
        
        event_bus.subscribe(MESSAGE_EVENT, async_bad, priority=100)
        event_bus.subscribe(MESSAGE_EVENT, async_good, priority=1)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        assert "async_good" in results


# =============================================================================
# 事件订阅/取消订阅测试
# =============================================================================

class TestSubscriptionManagement:
    """订阅管理测试"""
    
    @pytest.mark.asyncio
    async def test_unsubscribe_handler(self, event_bus, mock_api, sample_message_event):
        """测试取消订阅"""
        results = []
        
        def handler(e):
            results.append("called")
        
        # 订阅并获取 ID
        handler_id = event_bus.subscribe(MESSAGE_EVENT, handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        
        # 第一次分发 - 应该调用
        await dispatcher.dispatch(sample_message_event)
        assert results == ["called"]
        
        # 取消订阅
        event_bus.unsubscribe(handler_id)
        
        # 第二次分发 - 不应该调用
        await dispatcher.dispatch(sample_message_event)
        assert results == ["called"]  # 仍然只有一次调用
    
    @pytest.mark.asyncio
    async def test_regex_subscription(self, event_bus, mock_api, sample_message_event, sample_notice_event):
        """测试正则表达式订阅"""
        message_results = []
        all_results = []
        
        def message_handler(e):
            message_results.append(e.type)
        
        def all_handler(e):
            all_results.append(e.type)
        
        # 精确匹配消息事件
        event_bus.subscribe(MESSAGE_EVENT, message_handler)
        # 正则匹配所有 ncatbot 事件
        event_bus.subscribe("re:ncatbot\\..*", all_handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        
        await dispatcher.dispatch(sample_message_event)
        await dispatcher.dispatch(sample_notice_event)
        
        # 精确匹配只收到消息事件
        assert message_results == [MESSAGE_EVENT]
        # 正则匹配收到两个事件
        assert len(all_results) == 2


# =============================================================================
# 事件数据绑定测试
# =============================================================================

class TestEventDataBinding:
    """事件数据绑定测试"""
    
    @pytest.mark.asyncio
    async def test_api_bound_to_event(self, event_bus, mock_api, sample_message_event):
        """测试 API 被正确绑定到事件"""
        captured_event = None
        
        def handler(e):
            nonlocal captured_event
            captured_event = e
        
        event_bus.subscribe(MESSAGE_EVENT, handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        # 事件的内部数据应该有 API 绑定
        assert captured_event is not None
        assert hasattr(captured_event.data, 'api')
    
    @pytest.mark.asyncio
    async def test_event_reply_uses_bound_api(self, event_bus, mock_api, sample_message_event):
        """测试事件回复使用绑定的 API"""
        reply_done = False
        
        async def handler(e):
            nonlocal reply_done
            await e.data.reply("Test reply")
            reply_done = True
        
        event_bus.subscribe(MESSAGE_EVENT, handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        await dispatcher.dispatch(sample_message_event)
        
        assert reply_done
        # 验证 API 被调用
        call = mock_api.get_last_call()
        assert call is not None
        assert call[0] == "post_group_msg"
        assert call[2] == "Test reply"


# =============================================================================
# 批量事件处理测试
# =============================================================================

class TestBatchEventProcessing:
    """批量事件处理测试"""
    
    @pytest.mark.asyncio
    async def test_multiple_events_sequential(self, event_bus, mock_api):
        """测试顺序处理多个事件"""
        event_types = []
        
        def handler(e):
            event_types.append(e.type)
        
        event_bus.subscribe("re:ncatbot\\..*", handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        
        events = [
            {"time": 1767072511, "self_id": "123", "post_type": "message", "message_type": "group", 
             "message": [], "raw_message": "", "sender": {}, "group_id": "1", "user_id": "1", "message_id": "1"},
            {"time": 1767072512, "self_id": "123", "post_type": "notice", "notice_type": "group_increase", 
             "group_id": "1", "user_id": "1", "operator_id": "1"},
            {"time": 1767072513, "self_id": "123", "post_type": "request", "request_type": "friend", 
             "user_id": "1", "comment": "", "flag": "1"},
        ]
        
        for event_data in events:
            await dispatcher.dispatch(event_data)
        
        assert len(event_types) == 3
        assert MESSAGE_EVENT in event_types
        assert NOTICE_EVENT in event_types
        assert REQUEST_EVENT in event_types
    
    @pytest.mark.asyncio
    async def test_unknown_event_type_ignored(self, event_bus, mock_api):
        """测试未知事件类型被忽略"""
        results = []
        
        def handler(e):
            results.append(e)
        
        event_bus.subscribe("re:.*", handler)
        
        dispatcher = EventDispatcher(event_bus, mock_api)
        
        # 发送未知事件类型
        await dispatcher.dispatch({"post_type": "unknown_type", "data": "test"})
        
        # 不应该有任何处理器被调用
        assert len(results) == 0
