"""
TimeTaskMixin 集成测试和事件类型格式测试
"""

import time
import pytest

from ncatbot.core.service.builtin.time_task import TimeTaskService
from ncatbot.plugin_system.builtin_mixin.time_task_mixin import TimeTaskMixin
from .conftest import MockEventBus, MockBotClient, MockServiceManager


class TestTimeTaskMixinIntegration:
    """测试 TimeTaskMixin 集成（事件驱动机制）"""

    @pytest.mark.asyncio
    async def test_mixin_without_service_returns_false(self):
        """测试没有服务时 Mixin 返回 False"""

        class TestPlugin(TimeTaskMixin):
            name = "test_plugin"

        plugin = TestPlugin()

        def task():
            pass

        # 没有 _service_manager，应该返回 False
        result = plugin.add_scheduled_task(task, "mixin_task", "10s")
        assert result is False

    @pytest.mark.asyncio
    async def test_mixin_without_event_bus_returns_false(self):
        """测试没有事件总线时 Mixin 返回 False"""
        service = TimeTaskService()
        await service.on_load()

        class TestPlugin(TimeTaskMixin):
            name = "test_plugin"

        plugin = TestPlugin()
        plugin._service_manager = MockServiceManager(service)
        # 没有 _event_bus

        def task():
            pass

        try:
            result = plugin.add_scheduled_task(task, "mixin_task", "10s")
            assert result is False
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_mixin_with_service_and_event_bus(self):
        """测试有服务和事件总线时 Mixin 正常工作"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        await service.on_load()

        class TestPlugin(TimeTaskMixin):
            name = "test_plugin"

        plugin = TestPlugin()
        plugin._service_manager = MockServiceManager(service)
        plugin._event_bus = event_bus

        def task():
            pass

        try:
            result = plugin.add_scheduled_task(task, "mixin_task", "10s")
            assert result is True

            # 检查任务列表
            tasks = plugin.list_scheduled_tasks()
            assert "mixin_task" in tasks

            # 检查事件订阅是否正确注册
            event_type = "ncatbot.test_plugin.mixin_task"
            assert event_type in event_bus._handlers

            # 移除任务
            result = plugin.remove_scheduled_task("mixin_task")
            assert result is True

            tasks = plugin.list_scheduled_tasks()
            assert "mixin_task" not in tasks
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_mixin_static_dynamic_args_conflict(self):
        """测试静态参数和动态参数生成器冲突（在 Mixin 层检查）"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        await service.on_load()

        class TestPlugin(TimeTaskMixin):
            name = "test_plugin"

        plugin = TestPlugin()
        plugin._service_manager = MockServiceManager(service)
        plugin._event_bus = event_bus

        def task(x):
            pass

        def args_provider():
            return (1,)

        try:
            with pytest.raises(ValueError) as exc_info:
                plugin.add_scheduled_task(
                    task, "conflict_task", "10s", args=(1,), args_provider=args_provider
                )

            assert "静态参数和动态参数生成器不能同时使用" in str(exc_info.value)
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_mixin_event_execution(self):
        """测试事件驱动的任务执行"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        bot_client = MockBotClient(event_bus)
        service.service_manager = MockServiceManager(service, bot_client)
        await service.on_load()

        class TestPlugin(TimeTaskMixin):
            name = "test_plugin"

        plugin = TestPlugin()
        plugin._service_manager = MockServiceManager(service, bot_client)
        plugin._event_bus = event_bus

        executed = []

        def task():
            executed.append(True)

        try:
            result = plugin.add_scheduled_task(task, "exec_task", "1s")
            assert result is True

            # 等待调度器触发事件
            time.sleep(1.2)

            # 检查事件是否被发布
            assert len(event_bus._published_events) >= 1

            # 找到我们的任务事件
            task_events = [
                e
                for e in event_bus._published_events
                if e.type == "ncatbot.test_plugin.exec_task"
            ]
            assert len(task_events) >= 1

            # 任务应该被执行（通过事件处理器）
            assert len(executed) >= 1
        finally:
            await service.on_close()


class TestConditionChecks:
    """测试条件检查"""

    @pytest.mark.asyncio
    async def test_condition_false_skips_execution(self):
        """测试条件为 False 时跳过事件发布"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        bot_client = MockBotClient(event_bus)
        service.service_manager = MockServiceManager(service, bot_client)
        await service.on_load()

        def condition():
            return False

        try:
            service.add_job(
                "conditional_task",
                "1s",
                conditions=[condition],
                plugin_name="test",
            )

            # 等待调度
            time.sleep(1.2)

            # 事件不应该被发布
            task_events = [
                e for e in event_bus._published_events if "conditional_task" in e.type
            ]
            assert len(task_events) == 0
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_condition_true_publishes_event(self):
        """测试条件为 True 时发布事件"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        bot_client = MockBotClient(event_bus)
        service.service_manager = MockServiceManager(service, bot_client)
        await service.on_load()

        def condition():
            return True

        try:
            service.add_job(
                "conditional_task_true",
                "1s",
                conditions=[condition],
                plugin_name="test",
            )

            time.sleep(1.2)

            # 事件应该被发布
            task_events = [
                e
                for e in event_bus._published_events
                if "conditional_task_true" in e.type
            ]
            assert len(task_events) >= 1
        finally:
            await service.on_close()


class TestEventTypeFormat:
    """测试事件类型格式"""

    @pytest.mark.asyncio
    async def test_event_type_with_plugin_name(self):
        """测试带插件名称的事件类型格式"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        bot_client = MockBotClient(event_bus)
        service.service_manager = MockServiceManager(service, bot_client)
        await service.on_load()

        try:
            result = service.add_job(
                "my_task_with_plugin", "1s", plugin_name="my_plugin"
            )
            assert result is True

            time.sleep(1.5)

            # 检查事件类型格式
            task_events = [
                e
                for e in event_bus._published_events
                if "my_task_with_plugin" in e.type
            ]
            assert len(task_events) >= 1
            assert task_events[0].type == "ncatbot.my_plugin.my_task_with_plugin"
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_event_type_without_plugin_name(self):
        """测试不带插件名称的事件类型格式（默认使用 time_task）"""
        event_bus = MockEventBus()
        service = TimeTaskService()
        bot_client = MockBotClient(event_bus)
        service.service_manager = MockServiceManager(service, bot_client)
        await service.on_load()

        try:
            result = service.add_job("my_task_no_plugin", "1s")  # 不传 plugin_name
            assert result is True

            time.sleep(1.5)

            # 检查事件类型格式
            task_events = [
                e for e in event_bus._published_events if "my_task_no_plugin" in e.type
            ]
            assert len(task_events) >= 1
            assert task_events[0].type == "ncatbot.time_task.my_task_no_plugin"
        finally:
            await service.on_close()
