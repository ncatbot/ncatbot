"""QQ 通知事件实体"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ncatbot.types.qq.notice import (
    GroupIncreaseNoticeEventData,
    NoticeEventData,
)
from ncatbot.types.qq.enums import NoticeType

from ncatbot.event.common.base import BaseEvent
from ncatbot.event.common.mixins import GroupScoped, HasSender, Kickable

if TYPE_CHECKING:
    from ncatbot.api.qq import QQAPIClient

__all__ = [
    "NoticeEvent",
    "GroupIncreaseEvent",
]


class NoticeEvent(BaseEvent, HasSender, GroupScoped):
    """QQ 通知事件实体"""

    _data: NoticeEventData
    _api: QQAPIClient

    @property
    def api(self) -> QQAPIClient:
        return self._api

    @property
    def notice_type(self) -> NoticeType:
        return self._data.notice_type

    @property
    def group_id(self) -> Optional[str]:
        return self._data.group_id

    @property
    def user_id(self) -> Optional[str]:
        return self._data.user_id


class GroupIncreaseEvent(NoticeEvent, Kickable):
    """QQ 群成员增加事件"""

    _data: GroupIncreaseNoticeEventData

    @property
    def sub_type(self) -> str:
        return self._data.sub_type

    @property
    def operator_id(self) -> str:
        return self._data.operator_id

    async def kick(self, reject_add_request: bool = False) -> Any:
        return await self._api.set_group_kick(
            self._data.group_id, self._data.user_id, reject_add_request
        )
