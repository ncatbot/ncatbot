"""
配置混入类

管理插件 config.yaml 的加载、保存和便捷读写。
通过 _mixin_load / _mixin_unload 钩子自动参与插件生命周期。
"""

from pathlib import Path
from typing import Any, Dict, TYPE_CHECKING

import yaml

from ncatbot.utils import get_log

if TYPE_CHECKING:
    pass

LOG = get_log("ConfigMixin")


class ConfigMixin:
    """
    配置混入类

    - ``_mixin_load``: 从 config.yaml 加载配置到 ``self.config``
    - ``_mixin_unload``: 将 ``self.config`` 保存到 config.yaml
    - ``set_config`` / ``update_config``: 写时立即持久化

    使用示例::

        class MyPlugin(NcatBotPlugin):
            async def on_load(self):
                self.set_config("api_key", "default_key")
                key = self.get_config("api_key")
    """

    name: str
    workspace: Path
    config: Dict[str, Any]

    # ------------------------------------------------------------------
    # Mixin 钩子
    # ------------------------------------------------------------------

    def _mixin_load(self) -> None:
        """从 YAML 加载配置。"""
        self.config = self._load_config()

    def _mixin_unload(self) -> None:
        """将配置保存到 YAML。"""
        self._save_config()

    # ------------------------------------------------------------------
    # 持久化实现
    # ------------------------------------------------------------------

    @property
    def _config_path(self) -> Path:
        return self.workspace / "config.yaml"

    def _load_config(self) -> Dict[str, Any]:
        """从 YAML 加载配置，文件不存在则返回空字典。"""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    result = yaml.safe_load(f)
                    return result if isinstance(result, dict) else {}
            except Exception as e:
                LOG.error("加载插件 %s 配置失败: %s", self.name, e)
        return {}

    def _save_config(self) -> None:
        """将配置写入 YAML。"""
        try:
            self.workspace.mkdir(exist_ok=True, parents=True)
            with open(self._config_path, "w", encoding="utf-8") as f:
                yaml.safe_dump(
                    self.config, f, allow_unicode=True, default_flow_style=False
                )
        except Exception as e:
            LOG.error("保存插件 %s 配置失败: %s", self.name, e)

    # ------------------------------------------------------------------
    # 便捷接口
    # ------------------------------------------------------------------

    def get_config(self, key: str, default: Any = None) -> Any:
        """读取配置值。"""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """设置配置值并立即持久化。"""
        self.config[key] = value
        self._save_config()

    def remove_config(self, key: str) -> bool:
        """移除配置项并持久化，键不存在返回 False。"""
        if key in self.config:
            del self.config[key]
            self._save_config()
            return True
        return False

    def update_config(self, updates: Dict[str, Any]) -> None:
        """批量更新配置并持久化。"""
        self.config.update(updates)
        self._save_config()
