"""BotClient — Bot 统一入口（Composition Root）

负责引导 Adapter 启动、组装 BotAPIClient、接通事件流、管理服务生命周期。
作为应用编排层，允许依赖所有模块（core / plugin / service / api / adapter）。
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional, TYPE_CHECKING

from ncatbot.adapter.base import BaseAdapter
from ncatbot.adapter.napcat.adapter import NapCatAdapter
from ncatbot.api.client import BotAPIClient
from ncatbot.core.dispatcher import AsyncEventDispatcher
from ncatbot.core.registry import HandlerDispatcher
from ncatbot.plugin import PluginLoader
from ncatbot.service import ServiceManager
from ncatbot.utils import get_log, setup_logging

if TYPE_CHECKING:
    pass

LOG = get_log("BotClient")


class BotClient:
    """Bot 生命周期管理器

    用法::

        bot = BotClient()

        @bot.on("message.group")
        async def on_group_msg(event):
            await event.reply("hello")

        bot.run()
    """

    def __init__(
        self,
        adapter: Optional[BaseAdapter] = None,
        *,
        plugin_dir: str = "plugins",
        debug: bool = False,
    ) -> None:
        setup_logging()
        self._adapter = adapter or NapCatAdapter()
        self._api: Optional[BotAPIClient] = None
        self._dispatcher: Optional[AsyncEventDispatcher] = None
        self._handler_dispatcher: Optional[HandlerDispatcher] = None
        self._service_manager = ServiceManager()
        self._plugin_loader = PluginLoader(debug=debug)
        self._plugin_dir = Path(plugin_dir)
        self._debug = debug
        self._running = False
        self._listen_task: Optional[asyncio.Task] = None

        # 待注册的 handler（在 run 之前通过 @bot.on() 收集）
        self._pending_handlers: list[tuple[str, object, dict]] = []

    @property
    def plugin_loader(self) -> PluginLoader:
        return self._plugin_loader

    @property
    def service_manager(self) -> ServiceManager:
        return self._service_manager

    @property
    def api(self) -> BotAPIClient:
        if self._api is None:
            LOG.warning("API 不可用：BotClient 尚未启动")
            raise RuntimeError("API 不可用：BotClient 尚未启动")
        return self._api

    @property
    def dispatcher(self) -> AsyncEventDispatcher:
        if self._dispatcher is None:
            LOG.warning("Dispatcher 不可用：BotClient 尚未启动")
            raise RuntimeError("Dispatcher 不可用：BotClient 尚未启动")
        return self._dispatcher

    @property
    def handler_dispatcher(self) -> HandlerDispatcher:
        if self._handler_dispatcher is None:
            LOG.warning("HandlerDispatcher 不可用：BotClient 尚未启动")
            raise RuntimeError("HandlerDispatcher 不可用：BotClient 尚未启动")
        return self._handler_dispatcher

    # ---- 启动 ----

    def run(self) -> None:
        """同步阻塞启动（setup → connect → listen → shutdown）"""
        try:
            asyncio.run(self._run_blocking())
        except KeyboardInterrupt:
            LOG.info("收到 Ctrl+C，正在退出…")

    async def run_async(self) -> None:
        """异步非阻塞启动。

        完成 startup 后在后台启动监听，立即返回::

            bot = BotClient()
            await bot.run_async()
            # 此处 bot.api / bot.dispatcher 已可用
            async with bot.dispatcher.events(EventType.MESSAGE) as stream:
                async for event in stream:
                    ...
        """
        await self._startup()
        self._listen_task = asyncio.create_task(self._listen_forever())
        LOG.info("Bot 已就绪，后台监听已启动")

    async def shutdown(self) -> None:
        """关闭服务、Dispatcher 和 Adapter，释放资源。"""
        if not self._running:
            return
        self._running = False
        LOG.info("正在关闭…")
        try:
            if self._listen_task and not self._listen_task.done():
                self._listen_task.cancel()
                try:
                    await self._listen_task
                except asyncio.CancelledError:
                    pass
            # 停止热重载 + 卸载插件
            await self._plugin_loader.stop_hot_reload()
            await self._plugin_loader.unload_all()
            # 关闭服务
            await self._service_manager.close_all()
            # 关闭 HandlerDispatcher + AsyncEventDispatcher
            if self._handler_dispatcher is not None:
                await self._handler_dispatcher.stop()
            if self._dispatcher is not None:
                await self._dispatcher.close()
            await self._adapter.disconnect()
        except Exception as e:
            LOG.error("关闭异常: %s", e)
        LOG.info("已关闭")

    # ---- 内部 ----

    async def _run_blocking(self) -> None:
        """同步 run() 的内部实现：startup → 阻塞 listen → shutdown"""
        await self._startup()
        LOG.info("Bot 已就绪，开始监听事件")
        try:
            await self._adapter.listen()
        except asyncio.CancelledError:
            LOG.info("Bot 被取消")
        finally:
            await self.shutdown()

    async def _listen_forever(self) -> None:
        """后台监听 task，异常时自动 shutdown"""
        try:
            await self._adapter.listen()
        except asyncio.CancelledError:
            pass
        except Exception as e:
            LOG.error("监听异常: %s", e)
        finally:
            await self.shutdown()

    async def _startup(self) -> None:
        """引导启动：adapter → API → dispatcher → 服务 → 插件 → 热重载"""
        await self._startup_core()
        await self._setup_plugins()
        self._running = True

    async def _startup_core(self) -> None:
        """核心启动（不含插件加载）：adapter → API → dispatcher → 服务"""
        await self._setup_adapter()
        self._setup_api()
        self._setup_dispatcher()
        self._setup_handler_dispatcher()
        await self._setup_services()

    async def _setup_adapter(self) -> None:
        """准备并连接 Adapter。"""
        LOG.info("正在启动 Adapter: %s", self._adapter.name)
        await self._adapter.setup()
        await self._adapter.connect()

    def _setup_api(self) -> None:
        """从 Adapter 取出底层 IBotAPI，包装为 BotAPIClient。"""
        raw_api = self._adapter.get_api()
        self._api = BotAPIClient(raw_api)
        LOG.info("BotAPIClient 已就绪")

    def _setup_dispatcher(self) -> None:
        """创建事件分发器并接通 Adapter 事件回调。"""
        self._dispatcher = AsyncEventDispatcher()
        self._adapter.set_event_callback(self._dispatcher.callback)

    def _setup_handler_dispatcher(self) -> None:
        """创建 HandlerDispatcher 并订阅事件流。"""
        self._handler_dispatcher = HandlerDispatcher(
            api=self._api,
            service_manager=self._service_manager,
        )
        self._handler_dispatcher.start(self.dispatcher)

    async def _setup_services(self) -> None:
        """注册并加载所有内置服务。"""
        self._service_manager.set_event_callback(self.dispatcher.callback)
        self._service_manager.register_builtin(debug=self._debug)
        await self._service_manager.load_all()

    async def _setup_plugins(self) -> None:
        """加载插件并配置热重载。"""
        self._plugin_loader.set_handler_dispatcher(self.handler_dispatcher)

        def _inject_plugin_deps(plugin, manifest):
            plugin.services = self._service_manager
            plugin.api = self._api
            plugin._dispatcher = self._dispatcher
            plugin._plugin_loader = self._plugin_loader

        self._plugin_loader._on_plugin_init = _inject_plugin_deps
        await self._plugin_loader.load_builtin_plugins()
        await self._plugin_loader.load_all(self._plugin_dir)

        if self._debug and self._service_manager.has("file_watcher"):
            fw = self._service_manager.file_watcher
            fw.add_watch_dir(str(self._plugin_dir.resolve()))
            self._plugin_loader.setup_hot_reload(fw)
