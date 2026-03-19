import asyncio
from collections.abc import AsyncIterator
from types import TracebackType
from typing import Any, Self, cast

import pytest

from ncatbot import NcatBotApp, WaitEventCancelledError


class DummyEvent:
    pass


class IdleAdapter:
    @property
    def platform_name(self) -> str:
        return "dummy"

    @property
    def adapter_name(self) -> str:
        return "dummy.Adapter"

    @property
    def adapter_version(self) -> str:
        return "0"

    @property
    def base_event_type(self) -> type[DummyEvent]:
        return DummyEvent

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        return None

    def __aiter__(self) -> AsyncIterator[object]:
        async def iterator() -> AsyncIterator[object]:
            while True:
                await asyncio.sleep(3600)
                yield DummyEvent()

        return iterator()


def test_on_event_rejects_sync_handler_without_explicit_event_type() -> None:
    app = NcatBotApp()

    def sync_handler(event: DummyEvent) -> None:
        return None

    with pytest.raises(TypeError, match="async def"):
        app.on_event(cast(Any, sync_handler))


def test_on_event_rejects_sync_handler_with_explicit_event_type() -> None:
    app = NcatBotApp()

    def sync_handler(event: DummyEvent) -> None:
        return None

    decorator = app.on_event(DummyEvent)

    with pytest.raises(TypeError, match="async def"):
        decorator(cast(Any, sync_handler))


def test_on_event_rejects_explicit_handler_without_event_param() -> None:
    app = NcatBotApp()

    async def bad_handler() -> None:
        return None

    decorator = app.on_event(DummyEvent)

    with pytest.raises(TypeError, match="至少接收一个事件参数"):
        decorator(cast(Any, bad_handler))


def test_on_event_rejects_explicit_handler_with_extra_required_param() -> None:
    app = NcatBotApp()

    async def bad_handler(event: DummyEvent, extra: str) -> None:
        return None

    decorator = app.on_event(DummyEvent)

    with pytest.raises(TypeError, match="单个事件参数"):
        decorator(cast(Any, bad_handler))


def test_on_event_accepts_bound_async_method() -> None:
    app = NcatBotApp()

    class HandlerOwner:
        async def handle(self, event: DummyEvent) -> None:
            return None

    handler = HandlerOwner()
    app.on_event(handler.handle)

    assert app.handlers[DummyEvent] == [handler.handle]


def test_add_adapter_rejects_duplicate_instance() -> None:
    app = NcatBotApp()
    adapter = IdleAdapter()

    app.add_adapter(adapter)

    with pytest.raises(ValueError, match="重复添加"):
        app.add_adapter(adapter)


def test_wait_event_is_cancelled_when_app_stops() -> None:
    async def scenario() -> None:
        app = NcatBotApp()
        app.add_adapter(IdleAdapter())

        start_task = asyncio.create_task(app.start())
        await asyncio.sleep(0.05)

        waiter = asyncio.create_task(app.wait_event(lambda _: False))
        await asyncio.sleep(0.05)

        app.stop()
        await start_task

        with pytest.raises(WaitEventCancelledError, match="应用正在停止"):
            await waiter

    asyncio.run(scenario())
