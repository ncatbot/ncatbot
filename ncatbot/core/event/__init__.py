"""OneBot 11 事件系统

此模块提供了完整的 OneBot 11 标准事件解析和处理功能。
"""

# 导入所有子模块
from .message_segments import *  # noqa: F403
from .parser import EventParser
from .models import GroupSender, BaseSender

__all__ = [
    "EventParser",
    "GroupSender",
    "BaseSender",
]

# 动态导入子模块的 __all__
from . import message_segments
if hasattr(message_segments, "__all__"):
    __all__.extend(message_segments.__all__)


