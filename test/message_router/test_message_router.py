"""MessageRouter 单元测试

测试消息路由服务的核心逻辑：
- 消息区分（响应 vs 事件）
- 响应分发
- 生命周期管理
- 属性访问
"""

import asyncio
from queue import Queue
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncatbot.core.service.builtin.message_router import MessageRouter


class MockWebSocket:
    """模拟 NapCatWebSocket"""
    
    def __init__(self):
        self.connected = False
        self.sent_messages = []
        self._message_callback = None
    
    async def connect(self):
        self.connected = True
    
    async def disconnect(self):
        self.connected = False
    
    async def send(self, data: dict):
        self.sent_messages.append(data)
    
    def start_listening(self):
        return asyncio.Future()
    
    async def simulate_message(self, data: dict):
        """模拟收到消息"""
        if self._message_callback:
            await self._message_callback(data)


class TestMessageRouterInit:
    """测试 MessageRouter 初始化"""
    
    def test_init_default(self):
        """测试默认初始化"""
        router = MessageRouter()
        
        assert router._uri is None
        assert router._event_callback is None
        assert router._ws is None
        assert router._pending == {}
    
    def test_init_with_params(self):
        """测试带参数初始化"""
        callback = AsyncMock()
        router = MessageRouter(
            uri="ws://localhost:8080",
            event_callback=callback
        )
        
        assert router._uri == "ws://localhost:8080"
        assert router._event_callback == callback
    
    def test_properties(self):
        """测试属性"""
        router = MessageRouter()
        
        assert router.name == "message_router"
        assert router.description == "消息路由服务"


class TestMessageRouterLifecycle:
    """测试生命周期管理"""
    
    @pytest.mark.asyncio
    async def test_on_load_creates_connection(self):
        """测试 on_load 创建连接"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            assert router._ws is not None
            assert mock_ws.connected is True
    
    @pytest.mark.asyncio
    async def test_on_close_disconnects(self):
        """测试 on_close 断开连接"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            # 添加一些 pending 请求
            router._pending["test-echo"] = Queue()
            
            await router.on_close()
            
            assert router._ws is None
            assert router._pending == {}
            assert mock_ws.connected is False
    
    @pytest.mark.asyncio
    async def test_connected_property(self):
        """测试 connected 属性"""
        router = MessageRouter()
        assert router.connected is False
        
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            await router.on_load()
            assert router.connected is True
            
            await router.on_close()
            assert router.connected is False


class TestMessageRouterEventCallback:
    """测试事件回调"""
    
    def test_set_event_callback(self):
        """测试设置事件回调"""
        router = MessageRouter()
        callback = AsyncMock()
        
        router.set_event_callback(callback)
        
        assert router._event_callback == callback


class TestMessageDistinguishing:
    """测试消息区分逻辑"""
    
    @pytest.mark.asyncio
    async def test_message_with_echo_is_response(self):
        """测试带 echo 的消息被识别为响应"""
        router = MessageRouter()
        
        # 预设一个等待队列
        queue = Queue(maxsize=1)
        router._pending["test-echo-123"] = queue
        
        # 模拟收到响应
        response_data = {
            "echo": "test-echo-123",
            "retcode": 0,
            "data": {"result": "success"}
        }
        await router._on_message(response_data)
        
        # 响应应该被放入队列
        assert not queue.empty()
        assert queue.get() == response_data
    
    @pytest.mark.asyncio
    async def test_message_without_echo_is_event(self):
        """测试无 echo 的消息被识别为事件"""
        callback = AsyncMock()
        router = MessageRouter(event_callback=callback)
        
        # 模拟收到事件
        event_data = {
            "post_type": "message",
            "message_type": "group",
            "message": "test"
        }
        await router._on_message(event_data)
        
        # 事件应该触发回调
        callback.assert_called_once_with(event_data)
    
    @pytest.mark.asyncio
    async def test_event_without_callback_is_ignored(self):
        """测试没有回调时事件被忽略"""
        router = MessageRouter()  # 无回调
        
        event_data = {"post_type": "message"}
        # 不应该抛出异常
        await router._on_message(event_data)


class TestResponseDispatch:
    """测试响应分发"""
    
    def test_dispatch_response_to_correct_queue(self):
        """测试响应分发到正确的队列"""
        router = MessageRouter()
        
        queue1 = Queue(maxsize=1)
        queue2 = Queue(maxsize=1)
        router._pending["echo-1"] = queue1
        router._pending["echo-2"] = queue2
        
        # 分发响应
        router._dispatch_response({"echo": "echo-1", "data": "response1"})
        
        # 只有 queue1 收到响应
        assert not queue1.empty()
        assert queue2.empty()
        assert queue1.get()["data"] == "response1"
    
    def test_dispatch_response_unknown_echo_ignored(self):
        """测试未知 echo 的响应被忽略"""
        router = MessageRouter()
        
        # 不应该抛出异常
        router._dispatch_response({"echo": "unknown-echo", "data": "test"})
    
    def test_dispatch_response_empty_echo_ignored(self):
        """测试空 echo 被忽略"""
        router = MessageRouter()
        
        # 不应该抛出异常
        router._dispatch_response({"data": "test"})


class TestSendRequest:
    """测试发送请求"""
    
    @pytest.mark.asyncio
    async def test_send_without_connection_raises_error(self):
        """测试未连接时发送抛出错误"""
        router = MessageRouter()
        
        with pytest.raises(ConnectionError, match="服务未连接"):
            await router.send("get_login_info")
    
    @pytest.mark.asyncio
    async def test_send_creates_pending_entry(self):
        """测试发送创建 pending 条目"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            # 模拟响应（在发送后立即返回）
            async def respond_immediately():
                await asyncio.sleep(0.01)
                if mock_ws.sent_messages:
                    echo = mock_ws.sent_messages[0]["echo"]
                    router._dispatch_response({"echo": echo, "retcode": 0})
            
            asyncio.create_task(respond_immediately())
            
            response = await router.send("get_login_info", timeout=1.0)
            
            assert response["retcode"] == 0
    
    @pytest.mark.asyncio
    async def test_send_cleans_up_pending_on_success(self):
        """测试发送成功后清理 pending"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            async def respond():
                await asyncio.sleep(0.01)
                if mock_ws.sent_messages:
                    echo = mock_ws.sent_messages[0]["echo"]
                    router._dispatch_response({"echo": echo, "retcode": 0})
            
            asyncio.create_task(respond())
            
            await router.send("test_action", timeout=1.0)
            
            # pending 应该被清理
            assert len(router._pending) == 0
    
    @pytest.mark.asyncio
    async def test_send_message_format(self):
        """测试发送的消息格式"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            async def respond():
                await asyncio.sleep(0.01)
                if mock_ws.sent_messages:
                    echo = mock_ws.sent_messages[0]["echo"]
                    router._dispatch_response({"echo": echo, "retcode": 0})
            
            asyncio.create_task(respond())
            
            await router.send(
                "/send_msg",  # 带斜杠的 action
                params={"message": "test", "user_id": 123},
                timeout=1.0
            )
            
            sent = mock_ws.sent_messages[0]
            assert sent["action"] == "send_msg"  # 斜杠被移除
            assert sent["params"] == {"message": "test", "user_id": 123}
            assert "echo" in sent


class TestStartListening:
    """测试消息监听"""
    
    @pytest.mark.asyncio
    async def test_start_listening_with_ws(self):
        """测试有连接时启动监听"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            result = router.start_listening()
            
            assert result is not None
    
    def test_start_listening_without_ws(self):
        """测试无连接时启动监听返回 None"""
        router = MessageRouter()
        result = router.start_listening()
        assert result is None


class TestWebSocketProperty:
    """测试 websocket 属性"""
    
    def test_websocket_property_none(self):
        """测试未连接时返回 None"""
        router = MessageRouter()
        assert router.websocket is None
    
    @pytest.mark.asyncio
    async def test_websocket_property_returns_ws(self):
        """测试已连接时返回 WebSocket"""
        with patch(
            "ncatbot.core.service.builtin.message_router.NapCatWebSocket"
        ) as mock_ws_class:
            mock_ws = MockWebSocket()
            mock_ws_class.return_value = mock_ws
            
            router = MessageRouter(uri="ws://test:8080")
            await router.on_load()
            
            assert router.websocket is mock_ws

