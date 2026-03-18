"""Bilibili 平台专用事件实体"""

from .live import (
    BiliLiveEvent,
    DanmuMsgEvent,
    SuperChatEvent,
    GiftEvent,
    GuardBuyEvent,
    InteractEvent,
    LikeEvent,
    LiveNoticeEvent,
)
from .session import BiliPrivateMessageEvent, BiliPrivateMessageWithdrawEvent
from .comment import BiliCommentEvent
from .factory import create_bili_entity

# 自动注册 Bilibili 平台工厂到通用工厂
from ncatbot.event.common.factory import register_platform_factory as _register

_register("bilibili", create_bili_entity)
del _register

__all__ = [
    # live
    "BiliLiveEvent",
    "DanmuMsgEvent",
    "SuperChatEvent",
    "GiftEvent",
    "GuardBuyEvent",
    "InteractEvent",
    "LikeEvent",
    "LiveNoticeEvent",
    # session
    "BiliPrivateMessageEvent",
    "BiliPrivateMessageWithdrawEvent",
    # comment
    "BiliCommentEvent",
    # factory
    "create_bili_entity",
]
