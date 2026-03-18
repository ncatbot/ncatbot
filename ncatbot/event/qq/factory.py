"""QQ 平台事件工厂"""

from __future__ import annotations

from typing import TYPE_CHECKING, Dict, Optional, Type

from ncatbot.types.common.base import BaseEventData
from ncatbot.types.qq.enums import PostType
from ncatbot.types.qq.message import (
    GroupMessageEventData,
    PrivateMessageEventData,
)
from ncatbot.types.qq.notice import GroupIncreaseNoticeEventData
from ncatbot.types.qq.request import (
    FriendRequestEventData,
    GroupRequestEventData,
)

from ncatbot.event.common.base import BaseEvent
from .message import MessageEvent, GroupMessageEvent, PrivateMessageEvent
from .notice import NoticeEvent, GroupIncreaseEvent
from .request import FriendRequestEvent, GroupRequestEvent, RequestEvent
from .meta import MetaEvent

if TYPE_CHECKING:
    from ncatbot.api import IAPIClient

__all__ = [
    "create_qq_entity",
]

# 精确映射：数据模型类 → 实体类
_QQ_ENTITY_MAP: Dict[Type[BaseEventData], Type[BaseEvent]] = {
    PrivateMessageEventData: PrivateMessageEvent,
    GroupMessageEventData: GroupMessageEvent,
    FriendRequestEventData: FriendRequestEvent,
    GroupRequestEventData: GroupRequestEvent,
    GroupIncreaseNoticeEventData: GroupIncreaseEvent,
}

# post_type → 降级实体基类
_QQ_FALLBACK_MAP: Dict[str, Type[BaseEvent]] = {
    PostType.MESSAGE: MessageEvent,
    PostType.MESSAGE_SENT: MessageEvent,
    PostType.NOTICE: NoticeEvent,
    PostType.REQUEST: RequestEvent,
    PostType.META_EVENT: MetaEvent,
}


def create_qq_entity(data: BaseEventData, api: "IAPIClient") -> Optional[BaseEvent]:
    """QQ 平台事件工厂"""
    entity_cls = _QQ_ENTITY_MAP.get(type(data))
    if entity_cls is None:
        entity_cls = _QQ_FALLBACK_MAP.get(data.post_type)
    if entity_cls is None:
        return None
    return entity_cls(data, api)
