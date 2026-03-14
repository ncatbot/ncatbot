"""
定时任务测试的 fixtures 和 mock 类
"""

import asyncio
import pytest
from uuid import uuid4

from ncatbot.core.service.builtin.time_task import TimeTaskService


class MockEventBus:
    """模拟 EventBus"""

    def __init__(self):
        self._handlers = {}
        self._published_events = []

    def subscribe(self, event_type, handler, priority=0, timeout=None, plugin=None):
        handler_id = uuid4()
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append((handler_id, handler))
        return handler_id

    def unsubscribe(self, handler_id):
        for event_type in list(self._handlers.keys()):
            self._handlers[event_type] = [
                (hid, h) for hid, h in self._handlers[event_type] if hid != handler_id
            ]
        return True

    def publish_threadsafe_wait(self, event, timeout=None):
        """同步发布事件并执行处理器"""
        self._published_events.append(event)
        event_type = event.type
        if event_type in self._handlers:
            for _, handler in self._handlers[event_type]:
                if asyncio.iscoroutinefunction(handler):
                    # 在测试中同步运行协程
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.ensure_future(handler(event))
                        else:
                            loop.run_until_complete(handler(event))
                    except RuntimeError:
                        asyncio.run(handler(event))
                else:
                    handler(event)


class MockBotClient:
    """模拟 BotClient"""

    def __init__(self, event_bus):
        self.event_bus = event_bus


class MockServiceManager:
    """模拟 ServiceManager"""

    def __init__(self, time_task_service, bot_client=None):
        self._time_task = time_task_service
        self.bot_client = bot_client

    def get(self, name: str):
        if name == "time_task":
            return self._time_task
        return None


@pytest.fixture
def service():
    """创建 TimeTaskService 实例"""
    svc = TimeTaskService()
    svc.service_manager = None  # 没有 ServiceManager
    return svc


@pytest.fixture
async def running_service(service):
    """创建并启动服务"""
    await service.on_load()
    yield service
    await service.on_close()


@pytest.fixture
def event_bus():
    """创建模拟 EventBus"""
    return MockEventBus()


@pytest.fixture
def bot_client(event_bus):
    """创建模拟 BotClient"""
    return MockBotClient(event_bus)
