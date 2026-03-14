"""FunctionExecutor 单元测试

测试函数执行器的所有功能：
- 函数执行（同步/异步）
- 过滤器验证
- 插件上下文注入
- 缓存管理
"""

import pytest
from unittest.mock import Mock

from ncatbot.core.service.builtin.unified_registry.executor import FunctionExecutor
from ncatbot.core.service.builtin.unified_registry.filter_system.validator import (
    FilterValidator,
)


# =============================================================================
# 测试夹具
# =============================================================================


@pytest.fixture
def executor():
    """创建基本执行器"""
    return FunctionExecutor()


@pytest.fixture
def mock_event():
    """创建模拟事件"""
    event = Mock()
    event.message = Mock()
    event.user_id = 12345
    event.group_id = 67890
    return event


# =============================================================================
# FunctionExecutor 初始化测试
# =============================================================================


class TestFunctionExecutorInit:
    """测试执行器初始化"""

    def test_default_init(self):
        """测试默认初始化"""
        executor = FunctionExecutor()

        assert executor._filter_validator is not None
        assert isinstance(executor._filter_validator, FilterValidator)

    def test_custom_filter_validator(self):
        """测试自定义过滤器验证器"""
        custom_validator = Mock(spec=FilterValidator)
        executor = FunctionExecutor(filter_validator=custom_validator)

        assert executor._filter_validator is custom_validator


# =============================================================================
# 函数执行测试
# =============================================================================


class TestFunctionExecution:
    """测试函数执行"""

    @pytest.mark.asyncio
    async def test_execute_async_function(self, executor, mock_event):
        """测试执行异步函数"""
        result_holder = []

        async def async_handler(event):
            result_holder.append(event)
            return "success"

        result = await executor.execute(async_handler, None, mock_event)

        assert result == "success"
        assert len(result_holder) == 1
        assert result_holder[0] is mock_event

    @pytest.mark.asyncio
    async def test_execute_sync_function(self, executor, mock_event):
        """测试执行同步函数"""
        result_holder = []

        def sync_handler(event):
            result_holder.append(event)
            return "sync_success"

        result = await executor.execute(sync_handler, None, mock_event)

        assert result == "sync_success"
        assert len(result_holder) == 1

    @pytest.mark.asyncio
    async def test_execute_with_args(self, executor, mock_event):
        """测试带参数执行"""

        async def handler_with_args(event, arg1, arg2, kwarg1=None):
            return f"{arg1}-{arg2}-{kwarg1}"

        result = await executor.execute(
            handler_with_args, None, mock_event, "a", "b", kwarg1="c"
        )

        assert result == "a-b-c"

    @pytest.mark.asyncio
    async def test_execute_with_plugin_context(self, executor, mock_event):
        """测试带插件上下文执行"""

        class TestPlugin:
            def handler(self, event):
                return f"plugin:{self.__class__.__name__}"

        plugin_instance = TestPlugin()

        result = await executor.execute(TestPlugin.handler, plugin_instance, mock_event)

        assert result == "plugin:TestPlugin"

    @pytest.mark.asyncio
    async def test_execute_with_filter_validation_pass(self, executor, mock_event):
        """测试过滤器验证通过"""
        mock_validator = Mock(spec=FilterValidator)
        mock_validator.validate_filters.return_value = True
        executor._filter_validator = mock_validator

        async def filtered_handler(event):
            return "passed"

        filtered_handler.__filters__ = [Mock()]

        result = await executor.execute(filtered_handler, None, mock_event)

        assert result == "passed"
        mock_validator.validate_filters.assert_called_once()

    @pytest.mark.asyncio
    async def test_execute_with_filter_validation_fail(self, executor, mock_event):
        """测试过滤器验证失败"""
        mock_validator = Mock(spec=FilterValidator)
        mock_validator.validate_filters.return_value = False
        executor._filter_validator = mock_validator

        async def filtered_handler(event):
            return "should not reach"

        filtered_handler.__filters__ = [Mock()]

        result = await executor.execute(filtered_handler, Mock(), mock_event)

        assert result is False

    @pytest.mark.asyncio
    async def test_execute_handles_exception(self, executor, mock_event):
        """测试异常处理"""

        async def failing_handler(event):
            raise ValueError("Test error")

        result = await executor.execute(failing_handler, Mock(), mock_event)

        assert result is False


# =============================================================================
# 缓存管理测试
# =============================================================================
