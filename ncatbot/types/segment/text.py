from __future__ import annotations

from typing import ClassVar

from pydantic import field_validator

from .base import MessageSegment

__all__ = [
    "PlainText",
    "Face",
    "At",
    "Reply",
]


class PlainText(MessageSegment):
    _type: ClassVar[str] = "text"
    text: str


class Face(MessageSegment):
    _type: ClassVar[str] = "face"
    id: str

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, v: object) -> str:
        return str(v)


class At(MessageSegment):
    _type: ClassVar[str] = "at"
    qq: str

    @field_validator("qq", mode="before")
    @classmethod
    def _validate_qq(cls, v: object) -> str:
        s = str(v).strip()
        if s == "all" or s.isdigit():
            return s
        raise ValueError(f"At.qq 必须为纯数字或 'all'，收到: {v}")


class Reply(MessageSegment):
    _type: ClassVar[str] = "reply"
    id: str

    @field_validator("id", mode="before")
    @classmethod
    def _coerce_id(cls, v: object) -> str:
        return str(v)
