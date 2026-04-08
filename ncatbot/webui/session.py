"""Session management: HarnessProxy + SessionManager"""

from __future__ import annotations

import time
from typing import Callable
from uuid import uuid4

from ncatbot.testing.harness import TestHarness
from ncatbot.testing.plugin_harness import PluginTestHarness


# ---- Event type → factory function mapping ----


def _build_event(event_type: str, data: dict):
    """Map event_type string to factory function call."""
    from ncatbot.testing.factories import qq

    _FACTORY_MAP = {
        "message.group": qq.group_message,
        "message.private": qq.private_message,
        "request.friend": qq.friend_request,
        "request.group": qq.group_request,
        "notice.group_increase": qq.group_increase,
        "notice.group_decrease": qq.group_decrease,
        "notice.group_ban": qq.group_ban,
        "notice.group_upload": qq.group_upload,
        "notice.group_admin": qq.group_admin,
        "notice.group_recall": qq.group_recall,
        "notice.friend_recall": qq.friend_recall,
        "notice.poke": qq.poke,
        "notice.emoji_like": qq.group_msg_emoji_like,
    }
    factory = _FACTORY_MAP[event_type]  # KeyError if unknown
    return factory(**data)


class HarnessProxy:
    """WebUI ↔ TestHarness adapter.

    Wraps TestHarness lifecycle (start/stop instead of async-with)
    and adds real-time API call hooks for WebSocket push.
    """

    def __init__(
        self,
        platform: str = "qq",
        plugins: list[str] | None = None,
        plugins_dir: str | None = None,
    ):
        self._harness: TestHarness | None = None
        self._platform = platform
        self._plugins = plugins
        self._plugins_dir = plugins_dir
        self._api_call_hooks: list[Callable] = []
        self._call_index = 0  # track which calls have been seen

    async def start(self):
        """Start the underlying TestHarness."""
        if self._plugins:
            from pathlib import Path

            self._harness = PluginTestHarness(
                plugin_names=self._plugins,
                plugins_dir=Path(self._plugins_dir or "plugins"),
                platforms=(self._platform,),
            )
        else:
            self._harness = TestHarness(platforms=(self._platform,))
        await self._harness.start()
        self._install_api_hooks()

    async def stop(self):
        """Stop the underlying TestHarness."""
        if self._harness:
            await self._harness.stop()
            self._harness = None

    async def inject(self, event_type: str, data: dict):
        """Convert event_type + data → factory call → harness.inject()."""
        event_data = _build_event(event_type, data)
        await self._harness.inject(event_data)

    async def inject_raw(self, raw: dict):
        """Inject raw event data dict directly."""
        from ncatbot.event.common import BaseEventData

        event_data = BaseEventData.model_validate(raw)
        await self._harness.inject(event_data)

    async def settle(self) -> list[dict]:
        """Wait for handlers to finish, return new API calls since last settle."""
        await self._harness.settle()
        return self._drain_new_calls()

    def on_api_call(self, callback: Callable):
        """Register callback invoked on each API call: callback(action, params)."""
        self._api_call_hooks.append(callback)

    def _install_api_hooks(self):
        """Monkey-patch MockAPIBase._record to intercept API calls."""
        mock_api = self._harness.mock_api_for(self._platform)
        original_record = mock_api._record

        def hooked_record(action: str, **params):
            result = original_record(action, **params)
            for hook in self._api_call_hooks:
                hook(action, params)
            return result

        mock_api._record = hooked_record

    def _drain_new_calls(self) -> list[dict]:
        """Return API calls recorded since last drain."""
        mock_api = self._harness.mock_api_for(self._platform)
        all_calls = mock_api.calls
        new_calls = all_calls[self._call_index :]
        self._call_index = len(all_calls)
        return [{"action": c.action, "params": c.params} for c in new_calls]


class SessionManager:
    """Manage multiple independent WebUI test sessions."""

    SESSION_TIMEOUT = 1800  # 30 minutes

    def __init__(self):
        self._sessions: dict[str, HarnessProxy] = {}
        self._last_activity: dict[str, float] = {}

    async def create_session(
        self,
        platform: str = "qq",
        plugins: list[str] | None = None,
        plugins_dir: str | None = None,
    ) -> str:
        session_id = uuid4().hex[:8]
        proxy = HarnessProxy(platform, plugins, plugins_dir)
        await proxy.start()
        self._sessions[session_id] = proxy
        self._last_activity[session_id] = time.time()
        return session_id

    async def destroy_session(self, session_id: str):
        proxy = self._sessions.pop(session_id)  # KeyError if missing
        self._last_activity.pop(session_id, None)
        await proxy.stop()

    def get(self, session_id: str) -> HarnessProxy:
        proxy = self._sessions[session_id]  # KeyError if missing
        self._last_activity[session_id] = time.time()
        return proxy

    async def cleanup_expired(self):
        now = time.time()
        expired = [
            sid
            for sid, t in self._last_activity.items()
            if now - t > self.SESSION_TIMEOUT
        ]
        for sid in expired:
            try:
                await self.destroy_session(sid)
            except KeyError:
                pass

    async def destroy_all(self):
        for sid in list(self._sessions):
            try:
                await self.destroy_session(sid)
            except KeyError:
                pass
