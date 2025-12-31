"""
服务层

提供可动态加载/卸载的外部服务，支持依赖注入到插件和 API 组件。
"""

from .base import BaseService
from .manager import ServiceManager
from .builtin import (
    WebSocketService,
    StreamUploadClient,
    UploadResult,
    MessagePreUploadProcessor,
    ProcessResult,
    PreUploadResult,
    PreUploadService,
)

__all__ = [
    "BaseService",
    "ServiceManager",
    "WebSocketService",
    "StreamUploadClient",
    "UploadResult",
    "MessagePreUploadProcessor",
    "ProcessResult",
    "PreUploadResult",
    "PreUploadService",
]
