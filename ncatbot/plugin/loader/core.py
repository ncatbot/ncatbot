"""
插件加载器

组合 Indexer + Resolver + Importer，管理插件的完整生命周期。
通过 asyncio.create_task 订阅 FileWatcher 回调实现热重载。
"""

import asyncio
from pathlib import Path
from typing import Callable, Dict, List, Optional, Type, TYPE_CHECKING

from ncatbot.utils import get_log

from ..base import BasePlugin
from ..manifest import PluginManifest
from .indexer import PluginIndexer
from .resolver import DependencyResolver
from .importer import ModuleImporter

if TYPE_CHECKING:
    from ncatbot.core.registry.dispatcher import HandlerDispatcher

LOG = get_log("PluginLoader")


class PluginLoader:
    """插件加载器

    典型用法::

        loader = PluginLoader(debug=True)
        await loader.load_all(Path("plugins"))

        # 热重载由 setup_hot_reload 自动配置
    """

    def __init__(self, *, debug: bool = False) -> None:
        self._debug = debug
        self._indexer = PluginIndexer()
        self._resolver = DependencyResolver()
        self._importer = ModuleImporter()
        self.plugins: Dict[str, BasePlugin] = {}

        # 热重载相关
        self._reload_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reload_task: Optional[asyncio.Task] = None
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

        # 插件实例化时的注入回调（由外部设置）
        self._on_plugin_init: Optional[Callable[[BasePlugin, PluginManifest], None]] = (
            None
        )

        # Handler 分发器（由 BotClient 注入）
        self._handler_dispatcher: Optional["HandlerDispatcher"] = None

    # ------------------------------------------------------------------
    # 批量加载
    # ------------------------------------------------------------------

    async def load_all(self, plugin_dir: Path) -> List[str]:
        """扫描目录并按依赖顺序加载所有插件。

        Returns:
            成功加载的插件名列表
        """
        # 将插件根目录加入 sys.path（使跨插件导入可用）
        self._importer.add_plugin_root(plugin_dir)

        manifests = self._indexer.scan(plugin_dir)
        if not manifests:
            LOG.info("未在 %s 中发现插件", plugin_dir)
            return []

        # 依赖解析
        load_order = self._resolver.resolve(manifests)
        self._resolver.validate_versions(manifests)

        # 按序加载
        loaded = []
        for name in load_order:
            plugin = await self.load_plugin(name)
            if plugin is not None:
                loaded.append(name)

        LOG.info("已加载 %d/%d 个插件", len(loaded), len(manifests))
        return loaded

    # ------------------------------------------------------------------
    # 单个插件操作
    # ------------------------------------------------------------------

    def set_handler_dispatcher(self, dispatcher: "HandlerDispatcher") -> None:
        """注入 HandlerDispatcher 实例（由 BotClient 调用）。"""
        self._handler_dispatcher = dispatcher

    async def load_plugin(self, name: str) -> Optional[BasePlugin]:
        """加载单个插件（必须已索引）。"""
        from ncatbot.core.registry.context import (
            set_current_plugin,
            _current_plugin_ctx,
        )
        from ncatbot.core.registry.registrar import flush_pending, clear_pending

        manifest = self._indexer.get(name)
        if manifest is None:
            LOG.error("插件 %s 未索引，无法加载", name)
            return None

        try:
            # ContextVar 包裹模块加载，确保装饰器能读取到当前插件名
            token = set_current_plugin(name)
            try:
                module = self._importer.load_module(manifest)
            finally:
                _current_plugin_ctx.reset(token)

            plugin_class = self._importer.find_plugin_class(
                module, manifest.entry_class
            )
            plugin = self._instantiate(plugin_class, manifest)

            # 框架加载
            await plugin.__onload__()

            # 将装饰器收集的 handler 注册到 HandlerDispatcher
            if self._handler_dispatcher is not None:
                flush_pending(self._handler_dispatcher, name, plugin_instance=plugin)

            self.plugins[name] = plugin
            LOG.info("插件加载成功: %s v%s", name, manifest.version)
            return plugin

        except Exception as e:
            # 加载失败时清理残留的 pending handlers
            clear_pending(name)
            LOG.error("加载插件 %s 失败: %s", name, e)
            return None

    async def unload_plugin(self, name: str) -> bool:
        """卸载单个插件。"""
        from ncatbot.core.registry.registrar import clear_pending

        plugin = self.plugins.get(name)
        if plugin is None:
            LOG.warning("插件 %s 未加载", name)
            return False

        manifest = self._indexer.get(name)
        try:
            await plugin.__unload__()
        except Exception as e:
            LOG.error("插件 %s __unload__ 异常: %s", name, e)

        # 从 HandlerDispatcher 移除该插件的所有 handler
        if self._handler_dispatcher is not None:
            self._handler_dispatcher.revoke_plugin(name)

        # 清理可能残留的 pending handlers
        clear_pending(name)

        if manifest is not None:
            self._importer.unload_module(manifest)

        del self.plugins[name]
        LOG.info("插件已卸载: %s", name)
        return True

    async def reload_plugin(self, name: str) -> bool:
        """重载单个插件（卸载 → 重索引 → 加载）。"""
        manifest = self._indexer.get(name)
        if manifest is None:
            LOG.error("无法重载未索引的插件: %s", name)
            return False

        await self.unload_plugin(name)
        await asyncio.sleep(0.02)  # 等待清理完成

        # 重新读取 manifest（支持清单变更）
        new_manifest = self._indexer.rescan_plugin(name)
        if new_manifest is None:
            LOG.error("重载插件 %s 时重索引失败", name)
            return False

        result = await self.load_plugin(name)
        if result is not None:
            LOG.info("插件 %s 重载成功", name)
            return True
        return False

    async def unload_all(self) -> None:
        """卸载所有插件。"""
        await asyncio.gather(*(self.unload_plugin(name) for name in list(self.plugins)))

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------

    def get_plugin(self, name: str) -> Optional[BasePlugin]:
        return self.plugins.get(name)

    def list_plugins(self) -> List[str]:
        return list(self.plugins.keys())

    def get_plugin_name_by_folder(self, folder_name: str) -> Optional[str]:
        """根据文件夹名查找插件名。"""
        manifest = self._indexer.get_by_folder(folder_name)
        return manifest.name if manifest else None

    # ------------------------------------------------------------------
    # 热重载
    # ------------------------------------------------------------------

    def setup_hot_reload(
        self, file_watcher, *, loop: Optional[asyncio.AbstractEventLoop] = None
    ) -> None:
        """配置热重载。

        将 FileWatcherService 的回调连接到重载队列，并启动异步消费任务。

        Args:
            file_watcher: FileWatcherService 实例
            loop: 事件循环（默认使用当前 running loop）
        """
        self._event_loop = loop or asyncio.get_running_loop()

        def _on_change(plugin_folder: str):
            """FileWatcher 回调（在 watcher 线程中执行）"""
            assert self._event_loop is not None
            self._event_loop.call_soon_threadsafe(
                self._reload_queue.put_nowait, plugin_folder
            )

        file_watcher.on_file_changed = _on_change
        self._reload_task = asyncio.ensure_future(
            self._reload_consumer(), loop=self._event_loop
        )
        LOG.info("热重载已启动")

    async def stop_hot_reload(self) -> None:
        """停止热重载消费任务。"""
        if self._reload_task and not self._reload_task.done():
            self._reload_task.cancel()
            try:
                await self._reload_task
            except asyncio.CancelledError:
                pass
            self._reload_task = None
            LOG.info("热重载已停止")

    async def _reload_consumer(self) -> None:
        """异步任务：从队列中消费文件变更事件并执行重载。"""
        while True:
            folder_name = await self._reload_queue.get()
            plugin_name = self.get_plugin_name_by_folder(folder_name)
            if plugin_name is None:
                LOG.debug("未知插件目录: %s，跳过重载", folder_name)
                continue

            if plugin_name not in self.plugins:
                LOG.debug("插件 %s 未加载，跳过重载", plugin_name)
                continue

            LOG.info("热重载触发: %s (文件夹: %s)", plugin_name, folder_name)
            try:
                await self.reload_plugin(plugin_name)
            except Exception as e:
                LOG.error("热重载失败 [%s]: %s", plugin_name, e)

    # ------------------------------------------------------------------
    # 内置插件（预留，延后实现）
    # ------------------------------------------------------------------

    async def load_builtin_plugins(self) -> None:
        """加载内置插件（延后实现）。"""
        pass

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _instantiate(
        self, plugin_class: Type[BasePlugin], manifest: PluginManifest
    ) -> BasePlugin:
        """实例化插件并注入运行时属性。"""
        plugin = plugin_class()

        # 注入框架属性
        plugin._manifest = manifest
        plugin._debug = self._debug
        plugin.workspace = Path("data") / manifest.name
        plugin.config = {}
        plugin.data = {}

        # 外部注入回调
        if self._on_plugin_init:
            self._on_plugin_init(plugin, manifest)

        return plugin
