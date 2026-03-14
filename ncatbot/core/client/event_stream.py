"""
BotClient 事件流。

为 BotClient 提供按需订阅的异步事件流接口。
"""

from __future__ import annotations

import asyncio
import concurrent.futures
from typing import TYPE_CHECKING, Callable, Optional, TypeVar, Union

from ncatbot.utils import get_log

from ..event.enums import EventType
from .ncatbot_event import NcatBotEvent

if TYPE_CHECKING:
    from .event_bus import EventBus

T = TypeVar("T")
LOG = get_log("ClientEventStream")
_STOP = object()
_ALL_EVENTS = r"re:ncatbot\..*"


def normalize_event_stream_type(event_type: Optional[Union[str, EventType]]) -> str:
    """规范化事件流订阅类型。

    EventType 枚举会被映射到 EventBus 中实际发布的
    `ncatbot.{event_type.value}` 事件名；字符串则保持原样，
    因此同样支持 `re:` 正则订阅和前缀订阅。
    """

    if event_type is None:
        return _ALL_EVENTS

    if isinstance(event_type, EventType):
        return f"ncatbot.{event_type.value}"

    return event_type


class ClientEventStream:
    """BotClient 的一次性异步事件流订阅。

    每个实例都拥有独立的 EventBus 订阅。若需要确定性释放订阅，
    请优先使用 `async with` 或显式调用 :meth:`aclose`。
    """

    def __init__(
        self,
        event_bus: "EventBus",
        event_type: Optional[Union[str, EventType]] = None,
        *,
        priority: int = 0,
        timeout: Optional[float] = None,
    ) -> None:
        self._event_bus = event_bus
        self._event_type = normalize_event_stream_type(event_type)
        self._priority = priority
        self._timeout = timeout

        self._queue: Optional[asyncio.Queue[object]] = None
        self._consumer_loop: Optional[asyncio.AbstractEventLoop] = None
        self._handler_id = None
        self._opened = False
        self._closed = False

    @property
    def closed(self) -> bool:
        """当前订阅是否已关闭。"""

        return self._closed

    @property
    def event_type(self) -> str:
        """当前订阅的 EventBus 事件名。"""

        return self._event_type

    async def __aenter__(self) -> "ClientEventStream":
        await self._open()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def __aiter__(self) -> "ClientEventStream":
        return self

    async def __anext__(self) -> NcatBotEvent:
        if self._closed and (self._queue is None or self._queue.empty()):
            raise StopAsyncIteration

        await self._open()
        assert self._queue is not None

        item = await self._queue.get()
        if item is _STOP:
            raise StopAsyncIteration

        return item

    def __del__(self) -> None:
        try:
            self._close_sync()
        except Exception:  # pragma: no cover - 析构阶段只做兜底清理
            pass

    async def aclose(self) -> None:
        """关闭当前订阅并停止后续迭代。"""

        if self._closed:
            return

        self._closed = True

        if self._handler_id is not None:
            handler_id = self._handler_id
            self._handler_id = None
            await self._run_on_event_bus_loop(
                lambda: self._event_bus.unsubscribe(handler_id)
            )

        self._wake_consumer()

    async def _open(self) -> None:
        if self._opened:
            return

        if self._closed:
            raise RuntimeError("ClientEventStream 已关闭，请重新调用 bot.events()")

        self._consumer_loop = asyncio.get_running_loop()
        self._queue = asyncio.Queue()

        async def _handler(event: NcatBotEvent) -> None:
            if self._closed or self._consumer_loop is None or self._queue is None:
                return

            # 使用 loop-safe handoff，这样在后台线程运行 Bot 时也能把事件
            # 安全转交给消费方所在的事件循环。
            self._consumer_loop.call_soon_threadsafe(self._queue.put_nowait, event)

        self._handler_id = await self._run_on_event_bus_loop(
            lambda: self._event_bus.subscribe(
                self._event_type,
                _handler,
                priority=self._priority,
                timeout=self._timeout,
            )
        )
        self._opened = True

    def _close_sync(self) -> None:
        if self._closed:
            return

        self._closed = True

        if self._handler_id is not None:
            handler_id = self._handler_id
            self._handler_id = None

            event_loop = self._event_bus._loop
            if event_loop is not None and not event_loop.is_closed():
                event_loop.call_soon_threadsafe(self._event_bus.unsubscribe, handler_id)
            else:
                self._event_bus.unsubscribe(handler_id)

        self._wake_consumer()

    def _wake_consumer(self) -> None:
        if self._consumer_loop is None or self._queue is None:
            return
        if self._consumer_loop.is_closed():
            return

        self._consumer_loop.call_soon_threadsafe(self._queue.put_nowait, _STOP)

    async def _run_on_event_bus_loop(self, func: Callable[[], T]) -> T:
        """在 EventBus 绑定的事件循环上执行同步操作。"""

        event_loop = self._event_bus._loop
        current_loop = asyncio.get_running_loop()

        if (
            event_loop is None
            or event_loop == current_loop
            or event_loop.is_closed()
        ):
            return func()

        result: concurrent.futures.Future[T] = concurrent.futures.Future()

        def _runner() -> None:
            try:
                result.set_result(func())
            except Exception as exc:  # pragma: no cover - 防御性分支
                result.set_exception(exc)

        event_loop.call_soon_threadsafe(_runner)
        return await asyncio.wrap_future(result)


__all__ = ["ClientEventStream", "normalize_event_stream_type"]
