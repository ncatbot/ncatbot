"""跨平台通用事件基类、Mixin 与工厂"""

from .base import BaseEvent
from .factory import create_entity, register_platform_factory
from .mixins import (
    Approvable,
    Bannable,
    Deletable,
    GroupScoped,
    HasSender,
    Kickable,
    Replyable,
)

__all__ = [
    "BaseEvent",
    "create_entity",
    "register_platform_factory",
    # mixins
    "Replyable",
    "Deletable",
    "HasSender",
    "GroupScoped",
    "Kickable",
    "Bannable",
    "Approvable",
]
