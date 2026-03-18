"""QQ 平台专用事件实体"""

from .message import MessageEvent, PrivateMessageEvent, GroupMessageEvent
from .notice import NoticeEvent, GroupIncreaseEvent
from .request import RequestEvent, FriendRequestEvent, GroupRequestEvent
from .meta import MetaEvent
from .factory import create_qq_entity

# 自动注册 QQ 平台工厂到通用工厂
from ncatbot.event.common.factory import register_platform_factory as _register

_register("qq", create_qq_entity)
del _register

__all__ = [
    "MessageEvent",
    "PrivateMessageEvent",
    "GroupMessageEvent",
    "NoticeEvent",
    "GroupIncreaseEvent",
    "RequestEvent",
    "FriendRequestEvent",
    "GroupRequestEvent",
    "MetaEvent",
    "create_qq_entity",
]
