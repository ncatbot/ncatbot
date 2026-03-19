from collections.abc import AsyncIterator
from types import TracebackType
from typing import Protocol, Self, runtime_checkable


@runtime_checkable
class BaseAdapter(Protocol):
    """
    适配器协议
    """

    @property
    def platform_name(self) -> str: ...

    @property
    def adapter_name(self) -> str: ...

    @property
    def adapter_version(self) -> str: ...

    @property
    def base_event_type(self) -> type: ...

    async def __aenter__(self) -> Self: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ): ...

    def __aiter__(self) -> AsyncIterator[object]: ...
