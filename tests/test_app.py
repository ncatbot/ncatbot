from typing import Any, cast

import pytest

from ncatbot import NcatBotApp


class DummyEvent:
    pass


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


def test_on_event_accepts_bound_async_method() -> None:
    app = NcatBotApp()

    class HandlerOwner:
        async def handle(self, event: DummyEvent) -> None:
            return None

    handler = HandlerOwner()
    app.on_event(handler.handle)

    assert app.handlers[DummyEvent] == [handler.handle]
