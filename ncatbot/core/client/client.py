"""
Bot 客户端

组合各模块，提供统一的 Bot 客户端接口。
"""

from typing import AsyncGenerator, Callable, List, Optional, Type, TypeVar, TYPE_CHECKING

from ncatbot.utils import get_log
from ncatbot.utils.error import NcatBotError
from ncatbot.core.api.interface import IBotAPI
from ncatbot.core.service import ServiceManager
from ncatbot.core.service.builtin import (
    PluginConfigService,
    FileWatcherService,
    PluginDataService,
    TimeTaskService,
)
from ncatbot.core.registry import RegistryEngine
from ncatbot.adapter import BaseAdapter
from ncatbot.adapter.napcat import NapCatAdapter

from .event_bus import EventBus
from .dispatcher import EventDispatcher
from .registry import EventRegistry
from .lifecycle import LifecycleManager

if TYPE_CHECKING:
    from ncatbot.plugin_system import BasePlugin
    from ncatbot.core.event import BaseEvent

T = TypeVar("T")
LOG = get_log("Client")


class BotClient(EventRegistry, LifecycleManager):
    """
    Bot 客户端

    架构：
    ┌─────────────────────────────────────────────────────────┐
    │                       BotClient                         │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
    │  │ Services │  │ EventBus │  │ Registry │  │Lifecycle│ │
    │  │(服务层)   │ │(分发中心) │ │(注册接口)  │ │(生命周期)│ │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬────┘ │
    │       │             │             │             │       │
    │       └─────────────┴─────────────┴─────────────┘       │
    │                         ↓                               │
    │                    EventBus Callback                    │
    │                    (Adapter 事件入口)                    │
    └─────────────────────────────────────────────────────────┘

    事件流：
    Adapter → EventBus → Handlers/Plugins

    继承：
    - EventRegistry: 提供事件注册和装饰器接口

    测试模式：
    使用 start(mock=True) 启动 Mock 模式，连接到 MockServer。
    事件注入通过 MockServer.inject_event() 等方法实现。
    """

    _initialized = False

    def __init__(self, adapter: Optional[BaseAdapter] = None):
        """
        初始化 Bot 客户端

        Args:
            adapter: 平台适配器实例。默认使用 NapCatAdapter。
        """
        if BotClient._initialized:
            raise NcatBotError("BotClient 实例只能创建一次")
        BotClient._initialized = True

        # 1. 核心组件
        self.event_bus = EventBus()

        # 初始化父类 EventRegistry
        EventRegistry.__init__(self, self.event_bus)

        # 2. 注册引擎（直接订阅 EventBus）
        self.registry_engine = RegistryEngine()

        for event_type in (
            "ncatbot.group_message_event",
            "ncatbot.private_message_event",
            "ncatbot.message_sent_event",
        ):
            self.event_bus.subscribe(
                event_type,
                self._on_message_for_registry,
                priority=0,
            )
        for event_type in (
            "ncatbot.notice_event",
            "ncatbot.request_event",
            "ncatbot.meta_event",
        ):
            self.event_bus.subscribe(
                event_type,
                self._on_legacy_for_registry,
                priority=0,
            )

        # 3. 服务管理器（注入 EventBus）
        self.services = ServiceManager(event_bus=self.event_bus)
        self.services.set_bot_client(self)  # 过渡期兼容

        # 4. 注册内置服务（仅 5 个纯内部服务）
        self.services.register(PluginConfigService)
        self.services.register(FileWatcherService)
        self.services.register(PluginDataService)
        self.services.register(TimeTaskService)

        # 5. 适配器
        self.adapter: BaseAdapter = adapter or NapCatAdapter()

        # 6. API（延迟绑定，在 adapter.connect() 后获取）
        self.api: Optional[IBotAPI] = None

        # 事件分发器（延迟初始化）
        self.dispatcher: Optional[EventDispatcher] = None

        # 生命周期管理器
        LifecycleManager.__init__(self, self.services, self.event_bus, self)

        # 注册内置处理器
        self._register_builtin_handlers()

    @classmethod
    def reset_singleton(cls):
        """
        重置单例状态（仅用于测试）

        允许在测试中创建新的 BotClient 实例。
        """
        cls._initialized = False

    async def _setup_api(self) -> None:
        """设置 API（在 adapter.connect() 后调用）"""
        # 从适配器获取 IBotAPI
        self.api = self.adapter.get_api()

        # 保留一个薄分发器，便于测试和手动注入 dict 事件
        self.dispatcher = EventDispatcher(self.event_bus, self.api)

        # adapter 直接将标准事件交给 EventBus
        self.adapter.set_event_callback(self.event_bus.on_adapter_event)

        # 注入 BotClient 引用到 RegistryEngine（过渡期）
        self.registry_engine.set_bot_client(self)

    async def _on_message_for_registry(self, event) -> None:
        """EventBus 回调：消息事件 → RegistryEngine"""
        await self.registry_engine.handle_message_event(event.data)

    async def _on_legacy_for_registry(self, event) -> None:
        """EventBus 回调：通知/请求/元事件 → RegistryEngine"""
        await self.registry_engine.handle_legacy_event(event.data)

    def _register_builtin_handlers(self):
        """注册内置处理器"""
        @self.on_startup()
        async def _log_startup(event) -> None:
            LOG.info("Bot %s 启动成功", event.self_id)

    def events(self) -> AsyncGenerator["BaseEvent", None]:
        """按异步事件流消费 adapter 事件。"""
        return self.event_bus.events()

    def __aiter__(self) -> AsyncGenerator["BaseEvent", None]:
        return self.events()

    async def wait_event(
        self,
        predicate: Callable[["BaseEvent"], bool],
        timeout: Optional[float] = None,
    ) -> "BaseEvent":
        """等待下一条满足条件的 adapter 事件。"""
        return await self.event_bus.wait_event(predicate, timeout)

    # ==================== 工具方法 ====================

    def get_registered_plugins(self) -> List["BasePlugin"]:
        """获取已注册的插件列表"""
        if self.plugin_loader:
            return list(self.plugin_loader.plugins.values())
        return []

    def get_plugin(self, plugin_type: Type[T]) -> T:
        """获取指定类型的插件"""
        for plugin in self.get_registered_plugins():
            if isinstance(plugin, plugin_type):
                return plugin
        raise ValueError(f"插件 {plugin_type.__name__} 未找到")

    def get_plugin_class_by_name(self, plugin_name: str) -> Type["BasePlugin"]:
        """获取指定名称的插件类"""
        for plugin in self.get_registered_plugins():
            if plugin.name == plugin_name:
                return type(plugin)
        raise ValueError(f"插件 {plugin_name} 未找到")
