"""
异步事件总线

负责两类工作：
1. 接收 adapter 上报的标准 BaseEvent，并转为 NcatBotEvent 分发
2. 发布/消费框架内部自定义事件
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import uuid
from copy import copy
from dataclasses import dataclass
from inspect import isawaitable, iscoroutinefunction
from typing import TYPE_CHECKING, Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple

from ncatbot.utils import get_log

from ..event.enums import EventType, PostType
from ..event.events import BaseEvent
from .ncatbot_event import NcatBotEvent

if TYPE_CHECKING:
    from ncatbot.plugin_system import BasePlugin

LOG = get_log("EventBus")
_STOP = object()

AdapterEventPredicate = Callable[[BaseEvent], bool]


class HandlerTimeoutError(Exception):
    """保留旧异常类型，兼容仍引用该名字的代码。"""

    def __init__(self, meta_data: dict, handler: str, time: float):
        super().__init__()
        self.meta_data = meta_data
        self.handler = handler
        self.time = time

    def __str__(self) -> str:
        return f"来自 {self.meta_data['name']} 的处理器 {self.handler} 执行超时 {self.time}"


@dataclass(slots=True)
class _QueuedEvent:
    event: NcatBotEvent
    completion: asyncio.Future[List[Any]] | None = None
    adapter_event: BaseEvent | None = None


@dataclass(slots=True)
class _Waiter:
    token: object
    predicate: AdapterEventPredicate
    future: asyncio.Future[BaseEvent]


class EventBus:
    """
    异步事件总线。

    设计目标：
    - adapter 事件通过单一回调入口进入
    - 所有事件在单个分发协程中顺序处理，避免并发乱序
    - 为 BotClient 提供 `async for` 与 `wait_event` 能力
    """

    def __init__(
        self,
        default_timeout: float = 120,
        stream_queue_size: int = 500,
    ) -> None:
        # 复用旧字段名，减少外围代码的侵入式修改
        self._exact: Dict[str, List[Tuple[None, int, Callable[[NcatBotEvent], Any], uuid.UUID, float]]] = {}
        self._handler_meta: Dict[uuid.UUID, Dict[str, Any]] = {}
        self.default_timeout = default_timeout

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._incoming: asyncio.Queue[_QueuedEvent | object] = asyncio.Queue()
        self._dispatch_task: Optional[asyncio.Task[None]] = None
        self._startup_lock = asyncio.Lock()
        self._closed = False

        self._stream_queue_size = stream_queue_size
        self._stream_queues: set[asyncio.Queue[BaseEvent | object]] = set()
        self._waiters: List[_Waiter] = []

    def bind_loop(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        """绑定主事件循环，供跨线程发布使用。"""
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                LOG.warning("无法获取运行中的事件循环，跨线程发布将不可用")
                return
        self._loop = loop
        LOG.debug("EventBus 已绑定事件循环")

    def subscribe(
        self,
        event_type: str,
        handler: Callable[[NcatBotEvent], Any],
        priority: int = 0,
        timeout: Optional[float] = None,
        plugin: Optional["BasePlugin"] = None,
    ) -> uuid.UUID:
        """
        订阅事件处理程序。

        仅支持精确事件名匹配，处理器必须是异步函数。
        """
        if event_type.startswith("re:"):
            raise ValueError("EventBus 不再支持正则事件订阅")
        if not self._is_async_handler(handler):
            raise TypeError("EventBus 仅支持异步事件处理器")

        hid = uuid.uuid4()
        timeout_val = timeout if timeout is not None else self.default_timeout

        if plugin:
            self._handler_meta[hid] = plugin.meta_data

        bucket = self._exact.setdefault(event_type, [])
        bucket.append((None, priority, handler, hid, timeout_val))
        bucket.sort(key=lambda item: (-item[1], item[2].__name__))
        return hid

    def unsubscribe(self, handler_id: uuid.UUID) -> bool:
        """取消订阅事件处理程序。"""
        removed = False

        self._handler_meta.pop(handler_id, None)

        for event_type in list(self._exact.keys()):
            original_len = len(self._exact[event_type])
            self._exact[event_type] = [
                item for item in self._exact[event_type] if item[3] != handler_id
            ]
            removed |= len(self._exact[event_type]) != original_len
            if not self._exact[event_type]:
                del self._exact[event_type]

        return removed

    async def publish(self, event: NcatBotEvent) -> List[Any]:
        """发布自定义事件，并等待其处理完成。"""
        await self._ensure_runtime()

        loop = asyncio.get_running_loop()
        completion: asyncio.Future[List[Any]] = loop.create_future()
        await self._incoming.put(_QueuedEvent(event=event, completion=completion))
        return await completion

    async def on_adapter_event(self, event: BaseEvent, wait: bool = False) -> None:
        """adapter 事件入口：标准事件进入总线的唯一回调。"""
        await self._ensure_runtime()

        event_type = self._get_event_type_from_event(event)
        if event_type is None:
            LOG.debug("忽略未知事件类型: %s", getattr(event, "post_type", None))
            return

        completion: asyncio.Future[List[Any]] | None = None
        if wait:
            completion = asyncio.get_running_loop().create_future()

        await self._incoming.put(
            _QueuedEvent(
                event=NcatBotEvent(f"ncatbot.{event_type.value}", event),
                completion=completion,
                adapter_event=event,
            )
        )

        if completion is not None:
            await completion

    async def wait_event(
        self,
        predicate: AdapterEventPredicate,
        timeout: Optional[float] = None,
    ) -> BaseEvent:
        """等待下一条满足条件的 adapter 事件。"""
        await self._ensure_runtime()

        loop = asyncio.get_running_loop()
        token = object()
        future: asyncio.Future[BaseEvent] = loop.create_future()
        self._waiters.append(_Waiter(token=token, predicate=predicate, future=future))

        try:
            if timeout is None:
                return await future
            return await asyncio.wait_for(future, timeout)
        finally:
            self._remove_waiter(token)

    async def events(self) -> AsyncGenerator[BaseEvent, None]:
        """按事件流方式消费 adapter 事件。"""
        await self._ensure_runtime()

        queue: asyncio.Queue[BaseEvent | object] = asyncio.Queue(
            maxsize=self._stream_queue_size
        )
        self._stream_queues.add(queue)
        try:
            while True:
                item = await queue.get()
                if item is _STOP:
                    break
                if isinstance(item, BaseEvent):
                    yield item
        finally:
            self._stream_queues.discard(queue)

    def __aiter__(self) -> AsyncGenerator[BaseEvent, None]:
        return self.events()

    def publish_threadsafe(
        self, event: NcatBotEvent
    ) -> Optional[concurrent.futures.Future[List[Any]]]:
        """从非事件循环线程安全地发布自定义事件。"""
        if self._loop is None or self._loop.is_closed():
            LOG.warning("事件循环不可用，无法发布事件")
            return None
        return asyncio.run_coroutine_threadsafe(self.publish(event), self._loop)

    def publish_threadsafe_wait(
        self,
        event: NcatBotEvent,
        timeout: Optional[float] = 5.0,
    ) -> Optional[List[Any]]:
        """从非事件循环线程发布自定义事件并阻塞等待结果。"""
        future = self.publish_threadsafe(event)
        if future is None:
            return None

        try:
            return future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            LOG.error("事件发布超时: %s", event.type)
            return None
        except Exception as exc:
            LOG.error("事件发布失败: %s", exc)
            return None

    async def close(self) -> None:
        """异步关闭事件总线。"""
        if self._closed:
            return

        self._closed = True

        if self._dispatch_task and not self._dispatch_task.done():
            await self._incoming.put(_STOP)
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass
        else:
            self._finalize_shutdown()

    def shutdown(self) -> None:
        """同步关闭，仅适用于尚未启动分发协程的场景。"""
        self._closed = True
        if self._dispatch_task and not self._dispatch_task.done():
            self._dispatch_task.cancel()
            return
        self._finalize_shutdown()

    async def _ensure_runtime(self) -> None:
        if self._closed:
            raise RuntimeError("EventBus 已关闭")

        loop = asyncio.get_running_loop()
        if self._loop is None:
            self._loop = loop
        elif self._loop is not loop:
            raise RuntimeError("EventBus 不能跨多个事件循环复用")

        if self._dispatch_task and not self._dispatch_task.done():
            return

        async with self._startup_lock:
            if self._dispatch_task and not self._dispatch_task.done():
                return
            self._dispatch_task = asyncio.create_task(self._dispatch_loop())

    async def _dispatch_loop(self) -> None:
        try:
            while True:
                queued = await self._incoming.get()
                if queued is _STOP:
                    break

                assert isinstance(queued, _QueuedEvent)

                if queued.adapter_event is not None:
                    self._broadcast_adapter_event(queued.adapter_event)
                    self._resolve_waiters(queued.adapter_event)

                results = await self._dispatch_handlers(queued.event)
                if queued.completion is not None and not queued.completion.done():
                    queued.completion.set_result(results)
        except asyncio.CancelledError:
            raise
        finally:
            self._finalize_shutdown()

    async def _dispatch_handlers(self, event: NcatBotEvent) -> List[Any]:
        LOG.debug(
            "发布事件: %s 数据: %s",
            event.type,
            f"{str(event.data)[:50]}..." if len(str(event.data)) > 50 else str(event.data),
        )
        handlers = self._collect_handlers(event.type)

        for _, _, handler, _, _ in handlers:
            if event._propagation_stopped:
                break

            try:
                result = await self._run_handler(handler, event)
                event.add_result(result)
            except Exception as exc:
                LOG.exception("处理器 %s 执行失败: %s", handler.__name__, exc)
                event.add_exception(exc)

        return event.results

    async def _run_handler(
        self,
        handler: Callable[[NcatBotEvent], Any],
        event: NcatBotEvent,
    ) -> Any:
        result = handler(event)
        if not isawaitable(result):
            raise TypeError("EventBus 仅支持异步事件处理器")
        return await result

    def _collect_handlers(
        self,
        event_type: str,
    ) -> List[Tuple[None, int, Callable[[NcatBotEvent], Any], uuid.UUID, float]]:
        return list(self._exact.get(event_type, ()))

    def _broadcast_adapter_event(self, event: BaseEvent) -> None:
        for queue in tuple(self._stream_queues):
            if queue.full():
                try:
                    queue.get_nowait()
                    LOG.debug("事件流队列已满，已丢弃最旧事件")
                except asyncio.QueueEmpty:
                    pass
            try:
                queue.put_nowait(copy(event))
            except Exception:
                LOG.exception("写入事件流队列失败")

    def _resolve_waiters(self, event: BaseEvent) -> None:
        for waiter in tuple(self._waiters):
            if waiter.future.done():
                continue

            try:
                matched = bool(waiter.predicate(event))
            except Exception as exc:
                waiter.future.set_exception(exc)
                continue

            if matched:
                waiter.future.set_result(copy(event))

    def _remove_waiter(self, token: object) -> None:
        for index, waiter in enumerate(self._waiters):
            if waiter.token is token:
                del self._waiters[index]
                break

    def _finalize_shutdown(self) -> None:
        closed_error = RuntimeError("EventBus 已关闭")

        for waiter in self._waiters:
            if not waiter.future.done():
                waiter.future.set_exception(closed_error)
        self._waiters.clear()

        for queue in tuple(self._stream_queues):
            try:
                queue.put_nowait(_STOP)
            except Exception:
                pass
        self._stream_queues.clear()

        while not self._incoming.empty():
            try:
                queued = self._incoming.get_nowait()
            except asyncio.QueueEmpty:
                break
            if isinstance(queued, _QueuedEvent) and queued.completion is not None:
                if not queued.completion.done():
                    queued.completion.set_exception(closed_error)

        self._dispatch_task = None
        self._exact.clear()
        self._handler_meta.clear()
        self._loop = None

    @staticmethod
    def _is_async_handler(handler: Callable[[NcatBotEvent], Any]) -> bool:
        return iscoroutinefunction(handler) or iscoroutinefunction(
            getattr(handler, "__call__", None)
        )

    @staticmethod
    def _get_event_type_from_event(event: BaseEvent) -> Optional[EventType]:
        post_type = getattr(event, "post_type", None)
        if post_type == PostType.MESSAGE or post_type == "message":
            return EventType.MESSAGE
        if post_type == PostType.MESSAGE_SENT or post_type == "message_sent":
            return EventType.MESSAGE_SENT
        if post_type == PostType.NOTICE or post_type == "notice":
            return EventType.NOTICE
        if post_type == PostType.REQUEST or post_type == "request":
            return EventType.REQUEST
        if post_type == PostType.META_EVENT or post_type == "meta_event":
            return EventType.META
        return None
