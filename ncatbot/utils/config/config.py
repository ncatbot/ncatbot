from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from urllib.parse import quote_plus
import yaml
import os
from .base import BaseConfig
from .napcat import NapCatConfig
from .plugin import PluginConfig
from ncatbot.utils.logger import get_log
from .constants import CONFIG_PATH

logger = get_log("Config")


@dataclass(frozen=False)
class Config(BaseConfig):
    """NcatBot 配置类。"""

    napcat: NapCatConfig = field(default_factory=NapCatConfig)
    plugin: PluginConfig = field(default_factory=PluginConfig)

    _default_bt_uin: str = "123456"
    _default_root: str = "123456"

    root: str = _default_root
    bt_uin: str = _default_bt_uin
    enable_webui_interaction: bool = True
    debug: bool = False

    github_proxy: Optional[str] = field(
        default_factory=lambda: os.getenv("GITHUB_PROXY", None)
    )
    check_ncatbot_update: bool = True
    skip_ncatbot_install_check: bool = False
    websocket_timeout: int = 15

    def get_uri_with_token(self):
        quoted_token = quote_plus(self.napcat.ws_token)
        return f"{self.napcat.ws_uri.rstrip('/')}/?access_token={quoted_token}"

    def asdict(self) -> Dict[str, Any]:
        napcat = self.napcat.asdict()
        plugin = self.plugin.asdict()
        base = {
            k: v
            for k, v in self.__dict__.items()
            if isinstance(v, (str, int, bool, type(None), tuple, list))
            and not k.startswith("_")
        }
        return {**base, "napcat": napcat, "plugin": plugin}

    @classmethod
    def create_from_file(cls, path: str) -> "Config":
        try:
            with open(path, "r", encoding="utf-8") as f:
                conf_dict = yaml.safe_load(f)
                if conf_dict is None:
                    conf_dict = {}
        except FileNotFoundError as e:
            logger.warning("配置文件未找到")
            raise ValueError("[setting] 配置文件不存在！") from e
        except yaml.YAMLError as e:
            raise ValueError("[setting] 配置文件格式无效！") from e
        except Exception as e:
            raise ValueError(f"[setting] 未知错误: {e}") from e

        try:
            napcat_dict = conf_dict.get("napcat", {})
            plugin_dict = conf_dict.get("plugin", {})
            config = cls(
                napcat=NapCatConfig.from_dict(napcat_dict),
                plugin=PluginConfig.from_dict(plugin_dict),
            )

            for key, value in conf_dict.items():
                if key not in ATTRIBUTE_RECURSIVE:
                    if hasattr(config, key):
                        setattr(config, key, value)
                    else:
                        logger.warning(f"[setting] 未知配置项: {key}")

            return config
        except KeyError as e:
            raise KeyError(f"[setting] 缺少配置项: {e}") from e

    def __str__(self) -> str:
        return (
            f"[BOTQQ]: {self.bt_uin} | [WSURI]: {self.napcat.ws_uri} | "
            f"[WS_TOKEN]: {self.napcat.ws_token} | [ROOT]: {self.root} | "
            f"[WEBUI]: {self.napcat.webui_uri} | [WEBUI_TOKEN]: {self.napcat.webui_token}"
        )

    def update_from_file(self, path: str) -> None:
        new_config = self.create_from_file(path)
        self.__dict__.update(new_config.__dict__)

    def validate_config(self) -> None:
        self.bt_uin = str(self.bt_uin)
        self.root = str(self.root)

        if self.bt_uin == self._default_bt_uin:
            logger.warning("配置中未设置 QQ 号")
            self.bt_uin = str(input("请输入机器人 QQ 号: "))

        if self.root == self._default_root:
            logger.warning("未设置 root QQ 号，某些权限功能可能无法正常工作")

        logger.info(self)
        self.plugin.validate()
        self.napcat.validate()
        self.save()

    @classmethod
    def load(cls) -> "Config":
        try:
            logger.debug(f"从 {CONFIG_PATH} 加载配置")
            cfg = Config.create_from_file(CONFIG_PATH)
        except Exception as e:
            logger.error(f"加载配置失败: {e}")
            cfg = Config()
        return cfg

    def update_config(self, **kwargs: Any) -> None:
        for key, value in kwargs.items():
            if not self.update_value(key, value):
                logger.warning(f"[setting] 未知配置项: {key}")
        self.validate_config()

    def is_napcat_local(self) -> bool:
        return self.napcat.ws_host in ["localhost", "127.0.0.1"]

    # compatibility setters
    def set_bot_uin(self, bot_uin: str) -> None:
        self.bt_uin = str(bot_uin)

    def set_root(self, root: str) -> None:
        self.root = str(root)

    def set_ws_uri(self, ws_uri: str) -> None:
        self.napcat.ws_uri = str(ws_uri)

    def set_webui_uri(self, webui_uri: str) -> None:
        self.napcat.webui_uri = str(webui_uri)

    def set_ws_token(self, ws_token: str) -> None:
        self.napcat.ws_token = str(ws_token)

    def set_webui_token(self, webui_token: str) -> None:
        self.napcat.webui_token = str(webui_token)

    def set_ws_listen_ip(self, ws_listen_ip: str) -> None:
        self.napcat.ws_listen_ip = str(ws_listen_ip)


# ATTRIBUTE constants (defined here to reference NapCatConfig / PluginConfig)
ATTRIBUTE_RECURSIVE = {
    "napcat": NapCatConfig,
    "plugin": PluginConfig,
}

ATTRIBUTE_IGNORE = {
    "ws_host",
    "ws_port",
    "webui_host",
    "webui_port",
}

ncatbot_config = Config.load()
