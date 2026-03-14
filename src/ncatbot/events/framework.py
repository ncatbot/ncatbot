from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

type AdapterExitReason = Literal["completed", "failed", "stopped"]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True, frozen=True, kw_only=True)
class FrameworkEvent:
    emitted_at: datetime = field(default_factory=_utc_now)


@dataclass(slots=True, frozen=True, kw_only=True)
class AppEvent(FrameworkEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class AppStarting(AppEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class AppStarted(AppEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class AppStopping(AppEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterEvent(FrameworkEvent):
    adapter_name: str
    platform_name: str
    adapter_version: str


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterAdded(AdapterEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterRunEvent(AdapterEvent):
    attempt: int


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterRunStarting(AdapterRunEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterRunExited(AdapterRunEvent):
    reason: AdapterExitReason


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterRunFailed(AdapterRunEvent):
    exception: BaseException


@dataclass(slots=True, frozen=True, kw_only=True)
class AdapterRestartScheduled(AdapterRunEvent):
    delay: float


__all__ = [
    "AdapterAdded",
    "AdapterEvent",
    "AdapterExitReason",
    "AdapterRestartScheduled",
    "AdapterRunEvent",
    "AdapterRunExited",
    "AdapterRunFailed",
    "AdapterRunStarting",
    "AppEvent",
    "AppStarted",
    "AppStarting",
    "AppStopping",
    "FrameworkEvent",
]
