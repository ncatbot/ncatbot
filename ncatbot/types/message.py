from __future__ import annotations

from typing import Any, Optional

from pydantic import Field, field_validator

from .base import BaseEventData
from .enums import MessageType, PostType
from .misc import Anonymous
from .sender import BaseSender, GroupSender
from .segment.array import MessageArray

__all__ = [
    "MessageEventData",
    "PrivateMessageEventData",
    "GroupMessageEventData",
]


class MessageEventData(BaseEventData):
    post_type: PostType = Field(default=PostType.MESSAGE)
    message_type: MessageType
    sub_type: str
    message_id: str
    user_id: str
    message: MessageArray
    raw_message: str
    sender: BaseSender
    font: int = 0

    @field_validator("message", mode="before")
    @classmethod
    def _convert_message(cls, v: Any) -> MessageArray:
        if isinstance(v, list):
            return MessageArray.from_list(v)
        if isinstance(v, MessageArray):
            return v
        return MessageArray.from_any(v)


class PrivateMessageEventData(MessageEventData):
    message_type: MessageType = Field(default=MessageType.PRIVATE)
    sub_type: str = Field(default="friend")
    sender: BaseSender


class GroupMessageEventData(MessageEventData):
    message_type: MessageType = Field(default=MessageType.GROUP)
    sub_type: str = Field(default="normal")
    group_id: str
    anonymous: Optional[Anonymous] = None
    sender: GroupSender
