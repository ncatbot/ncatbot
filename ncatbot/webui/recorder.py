"""RecordingEngine — capture WebUI operations and export as Scenario DSL code"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RecordedStep:
    """A single recorded inject + settle pair."""

    event_type: str
    event_data: Dict[str, Any]
    api_calls: List[Dict[str, Any]]


# event_type → Scenario factory call name
_FACTORY_NAMES = {
    "message.group": "qq.group_message",
    "message.private": "qq.private_message",
    "request.friend": "qq.friend_request",
    "request.group": "qq.group_request",
    "notice.group_increase": "qq.group_increase",
    "notice.group_decrease": "qq.group_decrease",
    "notice.group_ban": "qq.group_ban",
    "notice.group_upload": "qq.group_upload",
    "notice.group_admin": "qq.group_admin",
    "notice.group_recall": "qq.group_recall",
    "notice.friend_recall": "qq.friend_recall",
    "notice.poke": "qq.poke",
    "notice.emoji_like": "qq.group_msg_emoji_like",
}


class RecordingEngine:
    """Record WebUI operations and export as Scenario DSL Python code."""

    def __init__(self) -> None:
        self._recording = False
        self._steps: List[RecordedStep] = []
        self._pending_event: Optional[Tuple[str, Dict[str, Any]]] = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def steps(self) -> List[RecordedStep]:
        return self._steps

    def start(self) -> None:
        self._recording = True
        self._steps.clear()
        self._pending_event = None

    def stop(self) -> None:
        self._recording = False

    def record_inject(self, event_type: str, event_data: Dict[str, Any]) -> None:
        if not self._recording:
            return
        self._pending_event = (event_type, event_data)

    def record_settle(self, api_calls: List[Dict[str, Any]]) -> None:
        if not self._recording or self._pending_event is None:
            return
        event_type, event_data = self._pending_event
        self._steps.append(
            RecordedStep(
                event_type=event_type,
                event_data=event_data,
                api_calls=api_calls,
            )
        )
        self._pending_event = None

    def export_scenario_dsl(self) -> str:
        lines = [
            "import pytest",
            "from ncatbot.testing import TestHarness, Scenario",
            "from ncatbot.testing.factories import qq",
            "",
            'pytestmark = pytest.mark.asyncio(mode="strict")',
            "",
            "",
            "async def test_recorded_scenario():",
            f'    """录制生成 - {datetime.now().strftime("%Y-%m-%d %H:%M")}"""',
            "    async with TestHarness() as h:",
            "        scenario = Scenario()",
        ]

        for i, step in enumerate(self._steps, 1):
            lines.append("")
            lines.append(f"        # Step {i}")
            factory_call = self._build_factory_call(step.event_type, step.event_data)
            lines.append(f"        scenario.inject({factory_call})")
            lines.append("        scenario.settle()")

            for call in step.api_calls:
                action = call["action"]
                lines.append(f'        scenario.assert_api_called("{action}")')
                text = self._extract_text(call)
                if text:
                    lines.append(
                        f'        scenario.assert_api_text("{action}", {text!r})'
                    )

        lines.append("")
        lines.append("        await scenario.run(h)")
        lines.append("")
        return "\n".join(lines)

    def _build_factory_call(self, event_type: str, data: Dict[str, Any]) -> str:
        name = _FACTORY_NAMES.get(event_type, f"qq.{event_type}")
        args = ", ".join(f"{k}={v!r}" for k, v in data.items())
        return f"{name}({args})"

    def _extract_text(self, call: Dict[str, Any]) -> Optional[str]:
        params = call.get("params", {})
        message = params.get("message", [])
        texts = []
        for seg in message:
            if isinstance(seg, dict) and seg.get("type") == "text":
                data = seg.get("data", {})
                texts.append(data.get("text", ""))
        return "".join(texts) if texts else None
