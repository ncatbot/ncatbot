"""BL-25: LiveSource 断线重连与停止状态测试"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ncatbot.adapter.bilibili.source.live_source import LiveSource

pytestmark = pytest.mark.asyncio(loop_scope="function")


async def test_bl25a_reconnects_with_new_danmaku_after_disconnect():
    """BL-25a: LiveSource 在 connect() 返回后创建新 LiveDanmaku 并继续连接"""
    collector = AsyncMock()
    source = LiveSource(
        room_id=123,
        credential=MagicMock(),
        callback=collector,
        retry_after=0.5,
    )

    first_danmaku = MagicMock()
    first_danmaku.connect = AsyncMock(return_value=None)

    async def _stop_after_second_connect() -> None:
        source._running = False

    second_danmaku = MagicMock()
    second_danmaku.connect = AsyncMock(side_effect=_stop_after_second_connect)

    source._danmaku = first_danmaku
    source._running = True

    with (
        patch.object(source, "_create_danmaku", return_value=second_danmaku) as factory,
        patch(
            "ncatbot.adapter.bilibili.source.live_source.asyncio.sleep",
            new=AsyncMock(),
        ) as sleep_mock,
    ):
        await source._connect_danmaku()

    first_danmaku.connect.assert_awaited_once_with()
    second_danmaku.connect.assert_awaited_once_with()
    factory.assert_called_once_with()
    sleep_mock.assert_awaited_once_with(0.5)
    assert source._ready.is_set()
    assert source._danmaku is second_danmaku


async def test_bl25b_stop_sets_stopping_before_disconnect_and_cleans_state():
    """BL-25b: stop() 在断开前设置 stopping 标记，并在完成后清理状态"""
    source = LiveSource(
        room_id=456,
        credential=MagicMock(),
        callback=AsyncMock(),
    )
    source._running = True

    danmaku = MagicMock()
    danmaku.disconnect.return_value = object()
    loop = MagicMock()
    thread = MagicMock()
    thread.is_alive.side_effect = [True, False]

    source._danmaku = danmaku
    source._loop = loop
    source._thread = thread

    future = MagicMock()

    def _assert_stopping_state(timeout: float) -> None:
        assert timeout == 10
        assert source._stopping is True
        assert source._running is False

    future.result.side_effect = _assert_stopping_state

    with patch(
        "ncatbot.adapter.bilibili.source.live_source.asyncio.run_coroutine_threadsafe",
        return_value=future,
    ) as run_coroutine_threadsafe:
        await source.stop()

    danmaku.disconnect.assert_called_once_with()
    run_coroutine_threadsafe.assert_called_once_with(
        danmaku.disconnect.return_value, loop
    )
    thread.join.assert_called_once_with(timeout=15)
    assert source._running is False
    assert source._stopping is False
    assert source._danmaku is None
    assert source._thread is None
    assert source._loop is None
