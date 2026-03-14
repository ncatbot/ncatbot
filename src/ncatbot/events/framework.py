from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal

type AdapterExitReason = Literal["completed", "failed", "stopped"]


def _utc_now() -> datetime:
    return datetime.now(UTC)


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


@dataclass(slots=True, frozen=True, kw_only=True)
class EventObservationEvent(FrameworkEvent):
    event_type: str
    is_framework_event: bool


@dataclass(slots=True, frozen=True, kw_only=True)
class EventReceived(AdapterEvent):
    event_type: str
    is_framework_event: bool


@dataclass(slots=True, frozen=True, kw_only=True)
class HandlersResolved(EventObservationEvent):
    handler_count: int
    handler_names: tuple[str, ...]


@dataclass(slots=True, frozen=True, kw_only=True)
class HandlerEvent(EventObservationEvent):
    handler_name: str


@dataclass(slots=True, frozen=True, kw_only=True)
class HandlerScheduled(HandlerEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class HandlerCompleted(HandlerEvent):
    duration_ms: float


@dataclass(slots=True, frozen=True, kw_only=True)
class HandlerFailed(HandlerEvent):
    duration_ms: float
    exception: BaseException


@dataclass(slots=True, frozen=True, kw_only=True)
class WaitLifecycleEvent(FrameworkEvent):
    waiter_id: int
    predicate_name: str
    timeout: float | None


@dataclass(slots=True, frozen=True, kw_only=True)
class WaitRegistered(WaitLifecycleEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class WaitMatched(WaitLifecycleEvent):
    event_type: str
    is_framework_event: bool


@dataclass(slots=True, frozen=True, kw_only=True)
class WaitTimedOut(WaitLifecycleEvent):
    pass


@dataclass(slots=True, frozen=True, kw_only=True)
class WaitCancelled(WaitLifecycleEvent):
    pass


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
    "EventObservationEvent",
    "EventReceived",
    "FrameworkEvent",
    "HandlerCompleted",
    "HandlerEvent",
    "HandlerFailed",
    "HandlerScheduled",
    "HandlersResolved",
    "WaitCancelled",
    "WaitLifecycleEvent",
    "WaitMatched",
    "WaitRegistered",
    "WaitTimedOut",
]
