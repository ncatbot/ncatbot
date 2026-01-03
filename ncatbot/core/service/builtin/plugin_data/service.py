"""
插件数据持久化服务

负责插件数据的加载和保存。
数据保存在 data/[plugin_name].json 文件中。
"""

import json
import aiofiles
from pathlib import Path
from typing import Any, Dict
from ...base import BaseService
from ncatbot.utils import get_log

LOG = get_log("PluginDataService")


class PluginDataService(BaseService):
    """插件数据持久化服务 - 管理插件数据的加载和保存"""

    name: str = "plugin_data"
    description: str = "插件数据持久化服务 - 管理插件数据的加载和保存"

    def __init__(self, **config: Any):
        super().__init__(**config)
        self._data_dir = Path("data")
        self._data_cache: Dict[str, Dict] = {}

    async def on_load(self) -> None:
        """服务加载"""
        self._data_dir.mkdir(exist_ok=True, parents=True)
        LOG.info("插件数据服务已加载，数据目录：%s", self._data_dir.absolute())

    async def on_close(self) -> None:
        """服务关闭 - 保存所有未保存的数据"""
        for plugin_name in list(self._data_cache.keys()):
            await self.save_plugin_data(plugin_name)
        LOG.info("插件数据服务已关闭")

    def _get_data_file(self, plugin_name: str) -> Path:
        """获取插件数据文件路径"""
        return self._data_dir / f"{plugin_name}.json"

    async def load_plugin_data(self, plugin_name: str) -> Dict:
        """
        加载插件数据

        Args:
            plugin_name: 插件名称

        Returns:
            插件数据字典，如果文件不存在则返回空字典
        """
        if plugin_name in self._data_cache:
            return self._data_cache[plugin_name]

        data_file = self._get_data_file(plugin_name)

        if not data_file.exists():
            LOG.debug(f"插件 {plugin_name} 的数据文件不存在，返回空字典")
            self._data_cache[plugin_name] = {}
            return self._data_cache[plugin_name]

        try:
            async with aiofiles.open(data_file, "r", encoding="utf-8") as f:
                content = await f.read()
                data = json.loads(content) if content.strip() else {}
                self._data_cache[plugin_name] = data
                LOG.info(f"成功加载插件 {plugin_name} 的数据")
                return data
        except json.JSONDecodeError as e:
            LOG.error(f"插件 {plugin_name} 的数据文件格式错误：{e}")
            self._data_cache[plugin_name] = {}
            return self._data_cache[plugin_name]
        except Exception as e:
            LOG.error(f"加载插件 {plugin_name} 的数据时出错：{e}")
            self._data_cache[plugin_name] = {}
            return self._data_cache[plugin_name]

    async def save_plugin_data(self, plugin_name: str) -> bool:
        """
        保存插件数据

        Args:
            plugin_name: 插件名称

        Returns:
            是否保存成功
        """
        if plugin_name not in self._data_cache:
            LOG.debug(f"插件 {plugin_name} 没有缓存数据，跳过保存")
            return True

        data_file = self._get_data_file(plugin_name)

        try:
            data_file.parent.mkdir(exist_ok=True, parents=True)

            async with aiofiles.open(data_file, "w", encoding="utf-8") as f:
                content = json.dumps(
                    self._data_cache[plugin_name], ensure_ascii=False, indent=2
                )
                await f.write(content)

            LOG.info(f"成功保存插件 {plugin_name} 的数据")
            return True
        except Exception as e:
            LOG.error(f"保存插件 {plugin_name} 的数据时出错：{e}")
            return False

    def get_plugin_data(self, plugin_name: str) -> Dict:
        """
        获取插件数据（从缓存）

        Args:
            plugin_name: 插件名称

        Returns:
            插件数据字典
        """
        if plugin_name not in self._data_cache:
            LOG.warning(f"插件 {plugin_name} 的数据尚未加载")
            return {}
        return self._data_cache[plugin_name]

    async def clear_plugin_data(self, plugin_name: str) -> bool:
        """
        清除插件数据（删除文件和缓存）

        Args:
            plugin_name: 插件名称

        Returns:
            是否清除成功
        """
        try:
            # 从缓存中删除
            if plugin_name in self._data_cache:
                del self._data_cache[plugin_name]

            # 删除文件
            data_file = self._get_data_file(plugin_name)
            if data_file.exists():
                data_file.unlink()
                LOG.info(f"成功清除插件 {plugin_name} 的数据")

            return True
        except Exception as e:
            LOG.error(f"清除插件 {plugin_name} 的数据时出错：{e}")
            return False
