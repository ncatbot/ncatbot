# 字面常量
from enum import Enum

WINDOWS_NAPCAT_DIR = "napcat"
LINUX_NAPCAT_DIR = "/opt/QQ/resources/app/app_launcher/napcat"

INSTALL_SCRIPT_URL = (
    "https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/install.sh"
)
NAPCAT_CLI_URL = (
    "https://nclatest.znin.net/NapNeko/NapCat-Installer/main/script/napcat_cli"
)
PYPI_URL = "https://mirrors.aliyun.com/pypi/simple/"

REQUEST_SUCCESS = "ok"
NAPCAT_WEBUI_SALT = "napcat"

OFFICIAL_GROUP_MESSAGE_EVENT = "ncatbot.group_message_event"
OFFICIAL_PRIVATE_MESSAGE_EVENT = "ncatbot.private_message_event"
OFFICIAL_MESSAGE_SENT_EVENT = "ncatbot.message_sent_event"
OFFICIAL_REQUEST_EVENT = "ncatbot.request_event"
OFFICIAL_NOTICE_EVENT = "ncatbot.notice_event"
OFFICIAL_STARTUP_EVENT = "ncatbot.startup_event"
OFFICIAL_SHUTDOWN_EVENT = "ncatbot.shutdown_event"
OFFICIAL_HEARTBEAT_EVENT = "ncatbot.heartbeat_event"

PLUGIN_BROKEN_MARK = "插件已损坏"


class PermissionGroup(Enum):
    # 权限组常量
    ROOT = "root"
    ADMIN = "admin"
    USER = "user"


class DefaultPermission(Enum):
    # 权限常量
    ACCESS = "access"
    SETADMIN = "setadmin"


EVENT_QUEUE_MAX_SIZE = 64  # 事件队列最大长度
PLUGINS_DIR = "plugins"  # 插件目录
META_CONFIG_PATH = None  # 元数据，所有插件一份(只读)
PERSISTENT_DIR = "data"  # 插件私有数据目录

__all__ = [
    "NAPCAT_WEBUI_SALT",
    "WINDOWS_NAPCAT_DIR",
    "LINUX_NAPCAT_DIR",
    "INSTALL_SCRIPT_URL",
    "NAPCAT_CLI_URL",
    "PYPI_URL",
    "REQUEST_SUCCESS",
    "OFFICIAL_GROUP_MESSAGE_EVENT",
    "OFFICIAL_PRIVATE_MESSAGE_EVENT",
    "OFFICIAL_MESSAGE_SENT_EVENT",
    "OFFICIAL_REQUEST_EVENT",
    "OFFICIAL_NOTICE_EVENT",
    "OFFICIAL_STARTUP_EVENT",
    "OFFICIAL_SHUTDOWN_EVENT",
    "OFFICIAL_HEARTBEAT_EVENT",
    "PLUGIN_BROKEN_MARK",
    "PermissionGroup",
    "DefaultPermission",
    "EVENT_QUEUE_MAX_SIZE",
    "PLUGINS_DIR",
    "META_CONFIG_PATH",
    "PERSISTENT_DIR",
]
