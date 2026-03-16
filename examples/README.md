# NcatBot 示例插件

> 覆盖框架全部核心功能和常见用户场景的示例插件集合。
> 每个插件都可以直接复制到 `plugins/` 目录中运行。

---

## 目录

### Phase 1：入门级（单一功能）

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 01 | [hello_world](01_hello_world/) | NcatBotPlugin 基类、manifest.toml、生命周期、消息回复 | ⭐ |
| 02 | [event_handling](02_event_handling/) | 三种事件消费模式（装饰器/事件流/wait_event） | ⭐ |
| 03 | [message_types](03_message_types/) | MessageArray 链式构造、图文混排、合并转发 | ⭐ |
| 04 | [config_and_data](04_config_and_data/) | ConfigMixin 配置持久化、DataMixin 数据持久化 | ⭐ |
| 05 | [bot_api](05_bot_api/) | Bot API 消息发送、群管理、信息查询 | ⭐ |

### Phase 2：进阶级（组合特性）

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 06 | [hook_and_filter](06_hook_and_filter/) | Hook 系统（BEFORE/AFTER/ON_ERROR）、内置过滤器 | ⭐⭐ |
| 07 | [rbac](07_rbac/) | RBAC 权限管理（角色/权限/用户绑定） | ⭐⭐ |
| 08 | [scheduled_tasks](08_scheduled_tasks/) | 定时任务（多种时间格式/条件执行） | ⭐⭐ |
| 09 | [notice_and_request](09_notice_and_request/) | 通知与请求事件（入群/退群/好友/撤回/戳） | ⭐⭐ |
| 10 | [multi_step_dialog](10_multi_step_dialog/) | 多步对话（连续交互/超时/取消） | ⭐⭐ |

### Phase 3：实战级（完整场景）

| # | 插件 | 演示功能 | 难度 |
|---|------|---------|------|
| 11 | [group_manager](11_group_manager/) | 群管理机器人（踢/禁言/欢迎/RBAC） | ⭐⭐⭐ |
| 12 | [qa_bot](12_qa_bot/) | 问答机器人（多步对话/关键词匹配/数据持久化） | ⭐⭐⭐ |
| 13 | [scheduled_reporter](13_scheduled_reporter/) | 定时统计报告（定时任务/合并转发/数据统计） | ⭐⭐⭐ |
| 14 | [external_api](14_external_api/) | 外部 API 集成（HTTP 请求/配置管理/错误处理） | ⭐⭐⭐ |
| 15 | [full_featured_bot](15_full_featured_bot/) | 全功能群助手（所有框架特性综合） | ⭐⭐⭐ |

---

## 使用方式

1. 将任意示例插件文件夹复制到项目根目录的 `plugins/` 下
2. 启动 Bot，插件自动加载

```text
plugins/
├── 01_hello_world/
│   ├── manifest.toml
│   └── main.py
```python

## 框架功能覆盖矩阵

| 框架功能 | 覆盖插件 |
|---------|---------|
| NcatBotPlugin + manifest.toml | 全部 |
| on_load / on_close 生命周期 | 01, 04, 07, 08, 15 |
| registrar.on / on_group_message | 01, 02, 05, 06 |
| registrar.on_notice / on_request | 09, 11, 15 |
| EventMixin.events() 事件流 | 02 |
| EventMixin.wait_event() | 02, 10, 12 |
| MessageArray 链式构造 | 03, 13 |
| 各类 MessageSegment | 03, 14 |
| Forward / ForwardConstructor | 03, 13 |
| api 消息发送 | 01, 05, 09, 11 |
| api.manage 群管理 | 05, 11 |
| api.info 查询 | 05, 13 |
| ConfigMixin | 04, 11, 14, 15 |
| DataMixin | 04, 10, 12, 13, 15 |
| RBACMixin | 07, 11, 15 |
| TimeTaskMixin | 08, 13, 15 |
| Hook（自定义） | 06, 12, 15 |
| 内置过滤器 | 06 |
| 多步对话 | 10, 12 |
| 外部 HTTP API | 14 |
| 错误处理 | 06, 14 |
