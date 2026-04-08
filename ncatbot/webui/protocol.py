"""WebSocket 消息协议定义"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---- 前端 → 后端 ----


@dataclass
class SessionCreatePayload:
    platform: str = "qq"
    plugins: Optional[List[str]] = None


@dataclass
class SessionDestroyPayload:
    session_id: str = ""


@dataclass
class EventInjectPayload:
    session_id: str = ""
    event_type: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EventInjectRawPayload:
    session_id: str = ""
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionSettlePayload:
    session_id: str = ""


@dataclass
class RecordingControlPayload:
    session_id: str = ""


@dataclass
class RecordingExportPayload:
    session_id: str = ""
    format: str = "scenario_dsl"


# ---- 后端 → 前端 ----


@dataclass
class APICallInfo:
    """一次 API 调用的序列化表示"""

    action: str = ""
    params: Dict[str, Any] = field(default_factory=dict)


# ---- 消息类型常量 ----


class MsgType:
    # 前端 → 后端
    SESSION_CREATE = "session.create"
    SESSION_DESTROY = "session.destroy"
    EVENT_INJECT = "event.inject"
    EVENT_INJECT_RAW = "event.inject_raw"
    SESSION_SETTLE = "session.settle"
    RECORDING_START = "recording.start"
    RECORDING_STOP = "recording.stop"
    RECORDING_EXPORT = "recording.export"

    # 后端 → 前端
    SESSION_CREATED = "session.created"
    API_CALLED = "api.called"
    SETTLE_DONE = "settle.done"
    RECORDING_EXPORTED = "recording.exported"
    ERROR = "error"


def make_response(msg_type: str, payload: dict, msg_id: Optional[str] = None) -> dict:
    """构造后端→前端的 JSON 消息"""
    msg: dict = {"type": msg_type, "payload": payload}
    if msg_id:
        msg["id"] = msg_id
    return msg
