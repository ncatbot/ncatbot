"""BotAPIClient — 对外暴露的胖客户端

高频 API 平铺在顶层，低频 API 按操作类型分到 manage / info / support。
"""

from __future__ import annotations

import asyncio
import functools
import json
from typing import Any, Union, cast

from .interface import IBotAPI
from ._sugar import MessageSugarMixin
from .extensions.manage import ManageExtension
from .extensions.info import InfoExtension
from .extensions.support import SupportExtension
from ncatbot.types.napcat import SendMessageResult, MessageHistory
from ncatbot.utils import get_log

LOG = get_log("BotAPIClient")

_LOG_TRUNCATE = 2000


class _LoggingAPIProxy:
    """IBotAPI 的日志代理，所有异步调用自动打 INFO 日志"""

    __slots__ = ("_real",)

    def __init__(self, real: IBotAPI) -> None:
        self._real = real

    def __getattr__(self, name: str) -> Any:
        attr = getattr(self._real, name)
        if not (asyncio.iscoroutinefunction(attr) or name.startswith("_")):
            return attr

        @functools.wraps(attr)
        async def _logged(*args: Any, **kwargs: Any) -> Any:
            s = _fmt_call(name, args, kwargs)
            LOG.debug(f"API调用 {s}")
            return await attr(*args, **kwargs)

        return _logged


def _fmt_call(name: str, args: tuple, kwargs: dict) -> str:
    parts = [name]
    for v in args:
        parts.append(_trunc(v))
    for k, v in kwargs.items():
        parts.append(f"{k}={_trunc(v)}")
    s = " ".join(parts)
    if len(s) > _LOG_TRUNCATE:
        s = s[:_LOG_TRUNCATE] + "..."
    return s


def _trunc(v: Any) -> str:
    if isinstance(v, (dict, list)):
        s = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
    else:
        s = str(v)
    if len(s) > _LOG_TRUNCATE:
        s = s[:_LOG_TRUNCATE] + "..."
    return s


class BotAPIClient(MessageSugarMixin):
    """插件开发者使用的 API 客户端

    高频操作直接调：
        await api.post_group_msg(group_id, text="hello")
        await api.delete_msg(message_id)

    低频操作走命名空间：
        await api.manage.set_group_ban(group_id, user_id, 600)
        await api.info.get_group_member_list(group_id)
        await api.support.upload_group_file(group_id, file, name)
    """

    def __init__(self, adapter_api: IBotAPI) -> None:
        logged = cast(IBotAPI, _LoggingAPIProxy(adapter_api))
        self._base = logged

        # 低频命名空间（同样走日志代理）
        self.manage = ManageExtension(logged)
        self.info = InfoExtension(logged)
        self.support = SupportExtension(logged)

    # ---- 高频原子 API（显式透传）----

    async def send_group_msg(
        self,
        group_id: Union[str, int],
        message: list,
        **kwargs: Any,
    ) -> SendMessageResult:
        return await self._base.send_group_msg(group_id, message, **kwargs)

    async def send_private_msg(
        self,
        user_id: Union[str, int],
        message: list,
        **kwargs: Any,
    ) -> SendMessageResult:
        return await self._base.send_private_msg(user_id, message, **kwargs)

    async def delete_msg(self, message_id: Union[str, int]) -> None:
        await self._base.delete_msg(message_id)

    async def send_forward_msg(
        self,
        message_type: str,
        target_id: Union[str, int],
        messages: list,
        **kwargs: Any,
    ) -> SendMessageResult:
        return await self._base.send_forward_msg(
            message_type,
            target_id,
            messages,
            **kwargs,
        )

    async def send_poke(
        self,
        group_id: Union[str, int],
        user_id: Union[str, int],
    ) -> None:
        await self._base.send_poke(group_id, user_id)

    # ---- 高频消息扩展 API（平铺到顶层）----

    async def get_group_msg_history(
        self,
        group_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        return await self._base.get_group_msg_history(group_id, message_seq, count)

    async def get_friend_msg_history(
        self,
        user_id: Union[str, int],
        message_seq: Union[str, int, None] = None,
        count: int = 20,
    ) -> MessageHistory:
        return await self._base.get_friend_msg_history(user_id, message_seq, count)

    async def set_msg_emoji_like(
        self,
        message_id: Union[str, int],
        emoji_id: str,
        set: bool = True,
    ) -> None:
        await self._base.set_msg_emoji_like(message_id, emoji_id, set)

    async def mark_group_msg_as_read(self, group_id: Union[str, int]) -> None:
        await self._base.mark_group_msg_as_read(group_id)

    async def mark_private_msg_as_read(self, user_id: Union[str, int]) -> None:
        await self._base.mark_private_msg_as_read(user_id)

    async def mark_all_as_read(self) -> None:
        await self._base.mark_all_as_read()

    async def forward_friend_single_msg(
        self, user_id: Union[str, int], message_id: Union[str, int]
    ) -> None:
        await self._base.forward_friend_single_msg(user_id, message_id)

    async def forward_group_single_msg(
        self, group_id: Union[str, int], message_id: Union[str, int]
    ) -> None:
        await self._base.forward_group_single_msg(group_id, message_id)

    async def friend_poke(self, user_id: Union[str, int]) -> None:
        await self._base.friend_poke(user_id)

    # ---- 兜底：未显式定义的方法代理到底层 ----

    def __getattr__(self, name: str) -> Any:
        return getattr(self._base, name)
