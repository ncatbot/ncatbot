from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator

from .enums import PostType

__all__ = [
    "BaseEventData",
]


class BaseEventData(BaseModel):
    """事件数据模型基类 — 纯数据，可序列化"""

    model_config = ConfigDict(extra="allow")

    time: int
    self_id: str
    post_type: PostType

    @model_validator(mode="before")
    @classmethod
    def _coerce_ids(cls, data: Any) -> Any:
        """统一将所有 *_id 字段从 int/float 转 str"""
        if isinstance(data, dict):
            for key, value in data.items():
                if key.endswith("_id") and isinstance(value, (int, float)):
                    data[key] = str(int(value))
        return data
