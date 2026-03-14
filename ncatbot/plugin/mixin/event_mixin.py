"""
事件消费混入类

代理 AsyncEventDispatcher 的 events() / wait_event() 接口，
通过 _mixin_unload 钩子在卸载时自动关闭所有活跃的 EventStream。
"""

from typing import Callable, List, Optional, Union, TYPE_CHECKING

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from ncatbot.core.dispatcher import AsyncEventDispatcher, Event
    from ncatbot.core.dispatcher.stream import EventStream
    from ncatbot.types.enums import EventType

LOG = get_log("EventMixin")


class EventMixin:
    """
    事件消费混入类

    - ``_mixin_unload``: 关闭所有活跃的 EventStream

    使用示例::

        async with self.events("message") as stream:
            async for event in stream:
                ...
    """

    _dispatcher: "AsyncEventDispatcher"

    def events(
        self,
        event_type: Optional[Union[str, "EventType"]] = None,
    ) -> "EventStream":
        """创建事件流，可选按类型过滤。

        返回的 EventStream 支持 async with / async for。
        插件卸载时框架会自动关闭所有未手动关闭的流。

        Args:
            event_type: 事件类型过滤（前缀匹配），如 "message"、"notice" 等

        Returns:
            EventStream 异步迭代器
        """
        stream = self._dispatcher.events(event_type)
        if not hasattr(self, "_active_streams"):
            self._active_streams: List["EventStream"] = []
        self._active_streams.append(stream)
        return stream

    async def wait_event(
        self,
        predicate: Optional[Callable[["Event"], bool]] = None,
        timeout: Optional[float] = None,
    ) -> "Event":
        """等待下一个满足条件的事件。

        Args:
            predicate: 过滤函数，None 表示接受任意事件
            timeout: 超时秒数，None 表示无限等待

        Returns:
            匹配的 Event

        Raises:
            asyncio.TimeoutError: 超时未匹配到事件
        """
        return await self._dispatcher.wait_event(predicate, timeout)

    # ------------------------------------------------------------------
    # Mixin 钩子
    # ------------------------------------------------------------------

    async def _mixin_unload(self) -> None:
        """关闭所有活跃的 EventStream。"""
        if not hasattr(self, "_active_streams"):
            return
        for stream in self._active_streams:
            try:
                await stream.aclose()
            except Exception:
                pass
        self._active_streams.clear()
