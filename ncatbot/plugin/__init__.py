"""
插件系统

提供插件基类、清单模型、加载器和完整插件基类。
"""

from .base import BasePlugin
from .manifest import PluginManifest
from .loader import PluginLoader
from .ncatbot_plugin import NcatBotPlugin

__all__ = [
    "BasePlugin",
    "NcatBotPlugin",
    "PluginManifest",
    "PluginLoader",
]
