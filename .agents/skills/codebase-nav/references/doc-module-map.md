# 文档-模块映射表

> 从文档路径到代码位置的完整对照，用于快速定位。

## guide/ → 代码模块

| 文档路径 | 对应代码模块 | 核心类/文件 |
|----------|-------------|------------|
| `guide/plugin/1.quick-start.md` | `ncatbot/plugin/` | `NcatBotPlugin` |
| `guide/plugin/2.structure.md` | `ncatbot/plugin/manifest.py` | `PluginManifest` |
| `guide/plugin/3.lifecycle.md` | `ncatbot/plugin/loader/` | `PluginLoader`, `PluginIndexer` |
| `guide/plugin/4a.event-registration.md` | `ncatbot/core/registry/` | `Registrar`, 装饰器 |
| `guide/plugin/4b.event-advanced.md` | `ncatbot/core/registry/` | `HandlerDispatcher` |
| `guide/plugin/5a.config-data.md` | `ncatbot/plugin/mixin/` | ConfigMixin, DataMixin |
| `guide/plugin/5b.rbac-schedule-event.md` | `ncatbot/plugin/mixin/` | RBACMixin, TimeTaskMixin |
| `guide/plugin/6.hooks.md` | `ncatbot/core/registry/` | Hook 机制与内置 Hook |
| `guide/plugin/7a.patterns.md` | 多个模块 | 综合 |
| `guide/plugin/7b.case-studies.md` | 多个模块 | 综合 |
| `guide/send_message/` | `ncatbot/api/`, `ncatbot/types/segment/` | `BotAPIClient`, 消息段 |
| `guide/api_usage/` | `ncatbot/api/` | `BotAPIClient`, extensions |
| `guide/configuration/` | `ncatbot/utils/config/` | `ConfigManager` |
| `guide/rbac/` | `ncatbot/service/builtin/` | RBAC 服务 |
| `guide/cli/` | `ncatbot/cli/` | `main.py`, commands |
| `guide/testing/` | `ncatbot/testing/` | `TestHarness` |

## reference/ → 代码模块

| 文档路径 | 对应代码模块 | 核心类/文件 |
|----------|-------------|------------|
| `reference/api/1_message_api.md` | `ncatbot/api/` | 消息发送方法 |
| `reference/api/2_manage_api.md` | `ncatbot/api/extensions/` | 群管理方法 |
| `reference/api/3_info_support_api.md` | `ncatbot/api/extensions/` | 查询/辅助方法 |
| `reference/events/1_event_classes.md` | `ncatbot/event/` | 事件类层级 |
| `reference/types/1_segments.md` | `ncatbot/types/segment/` | 消息段类型 |
| `reference/types/2_message_array.md` | `ncatbot/types/segment/` | `MessageArray` |
| `reference/types/3_response_types.md` | `ncatbot/types/napcat/` | API 响应类型 |
| `reference/core/1_internals.md` | `ncatbot/core/` | Dispatcher, Registry |
| `reference/plugin/1_base_class.md` | `ncatbot/plugin/base.py`, `ncatbot_plugin.py` | 基类 |
| `reference/plugin/2_mixins.md` | `ncatbot/plugin/mixin/` | Mixin 体系 |
| `reference/services/1_rbac_service.md` | `ncatbot/service/builtin/` | RBAC |
| `reference/services/2_config_task_service.md` | `ncatbot/service/builtin/` | Config, Schedule |
| `reference/adapter/1_connection.md` | `ncatbot/adapter/napcat/connection/` | WebSocket |
| `reference/adapter/2_protocol.md` | `ncatbot/adapter/napcat/` | OB11Protocol, Parser |
| `reference/utils/1a_io_logging.md` | `ncatbot/utils/logger/`, `ncatbot/utils/` | IO, Logger |
| `reference/utils/2_decorators_misc.md` | `ncatbot/utils/` | 装饰器工具 |
| `reference/testing/1_harness.md` | `ncatbot/testing/harness.py` | TestHarness |
| `reference/testing/2_factory_scenario_mock.md` | `ncatbot/testing/factory.py` | 工厂, Scenario |

## contributing/ → 代码模块

| 文档路径 | 覆盖的代码范围 |
|----------|--------------|
| `contributing/module_internals/1.core_modules.md` | `ncatbot/core/`, `ncatbot/app/`, `ncatbot/adapter/` |
| `contributing/module_internals/2.plugin_service_modules.md` | `ncatbot/plugin/`, `ncatbot/service/` |
| `contributing/design_decisions/1_architecture.md` | 跨模块架构决策 |
| `contributing/design_decisions/2_implementation.md` | Dispatcher / Hook / 热重载实现决策 |

## 关键词 → 文档快速跳转

| 关键词 | 直达文档 |
|--------|---------|
| 插件、Plugin、BasePlugin | `guide/plugin/README.md` |
| 事件、Event、handler、on_message | `guide/plugin/4a.event-registration.md` |
| Hook、Filter、中间件 | `guide/plugin/6.hooks.md` |
| 消息、发送、图片、语音 | `guide/send_message/README.md` |
| 消息段、Segment、MessageArray | `reference/types/1_segments.md` |
| 合并转发、Forward | `guide/send_message/4_forward.md` |
| API、BotAPIClient | `guide/api_usage/README.md` |
| 群管理、禁言、踢人 | `guide/api_usage/2_manage.md` |
| 配置、Config、yaml | `guide/configuration/README.md` |
| RBAC、权限、角色 | `guide/rbac/README.md` |
| CLI、命令行、ncatbot | `guide/cli/README.md` |
| 定时任务、Schedule | `reference/services/2_config_task_service.md` |
| 测试、Test、Harness | `guide/testing/README.md` |
| WebSocket、连接、断线 | `reference/adapter/1_connection.md` |
| 日志、Logger、log | `reference/utils/1a_io_logging.md` |
| Dispatcher、分发 | `reference/core/1_internals.md` |
| Registry、注册 | `reference/core/1_internals.md` |
| 生命周期、启动、关闭 | `docs/architecture.md`（§5 生命周期） |
