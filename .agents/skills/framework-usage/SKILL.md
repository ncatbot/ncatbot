---
name: framework-usage
description: '使用 NcatBot 框架开发 QQ 机器人或跨平台 Bot。当用户需要快速体验、创建插件、注册事件处理、发送消息、调用 Bot API、使用 Mixin/Hook、使用 CLI 工具、编写插件测试、或调试运行问题时触发此技能。Use when: 开发 bot、写插件、发消息、消息段、群管理、事件处理、响应命令、Mixin、Hook、定时任务、权限、RBAC、CLI、调试、插件测试、多平台、跨平台、platform。'
license: MIT
---

# 技能指令

你是 NcatBot 开发助手。帮助用户使用 NcatBot 框架开发 QQ 机器人或跨平台 Bot。

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 编写/运行/调试测试 | **testing-framework** |
| 定位框架内部代码、理解模块实现 | **codebase-nav** |
| 修框架 bug、改框架代码 | **framework-dev** |
| **用框架开发 bot** | **framework-usage**（本技能） |

---

## 工作流

```text
1. 选模式 → 2. 搭项目 → 3. 开发功能 → 4. 测试调试
```

### Step 1：选模式

| 场景 | 推荐模式 | 理由 |
|------|---------|------|
| 快速验证想法、体验框架 | **非插件模式** | 零配置，全写在 main.py |
| 简单 Bot、几个命令 | **非插件模式** | 最小代码量 |
| 需要持久化配置/数据 | **插件模式** | ConfigMixin / DataMixin |
| 需要定时任务、权限控制 | **插件模式** | TimeTaskMixin / RBACMixin |
| 多功能、可维护的正式项目 | **插件模式** | 热重载 + Mixin + 结构化 |

### Step 2：搭项目

详见 [getting-started.md](./references/getting-started.md)（安装、CLI、config.yaml 模板、最小代码示例）。

### Step 3：开发功能

根据用户需求查阅对应 reference：

| 用户需求 | 框架功能 | 参考 |
|---------|---------|------|
| 安装/搭建项目/CLI/配置 | 项目初始化 | [getting-started.md](./references/getting-started.md) |
| 响应命令/消息/事件 | 装饰器 + handler | [events.md](./references/events.md) |
| 简单命令处理 | CommandHook（单层命令） | [hooks.md](./references/hooks.md) |
| 分层命令结构（子命令/命令组） | CommandGroupHook | [hooks.md](./references/hooks.md) |
| 过滤/拦截/中间件 | Hook 系统 | [hooks.md](./references/hooks.md) |
| 发送文字/图片/视频/转发 | 消息构造与发送 | [messaging.md](./references/messaging.md) |
| 群管理/查询信息/文件/平台 API | Bot API | [bot-api.md](./references/bot-api.md) |
| 持久化配置/数据 | ConfigMixin / DataMixin | [mixins.md](./references/mixins.md) |
| 定时任务/权限控制/事件流 | TimeTaskMixin / RBACMixin / EventMixin | [mixins.md](./references/mixins.md) |
| 多步对话/等待回复 | wait_event / EventStream | [events.md](./references/events.md) |
| 非阻塞启动/事件编排 | run_async + wait_event + events() | [events.md](./references/events.md) |
| 多平台/跨平台/Trait | BotAPIClient 多平台门面, Trait 协议 | [multi-platform.md](./references/multi-platform.md) |
| 平台登录/适配器配置 | 各适配器登录流程 | [multi-platform.md](./references/multi-platform.md) |
| 插件结构/生命周期 | manifest + 基类 | [plugin-structure.md](./references/plugin-structure.md) |
| 调试/排错/日志 | 诊断与排查 | [troubleshooting.md](./references/troubleshooting.md) |

### Step 4：测试与调试

- **测试**：委托 **testing-framework** 技能（PluginTestHarness、事件工厂、Scenario）。
- **调试**：查阅 [troubleshooting.md](./references/troubleshooting.md)（日志、配置检查、常见问题）。
- **框架行为不符预期**：使用 **codebase-nav** 技能定位问题。

---

## 查资料的方法

### 简单问题 → 读 references/

`references/` 是常用 API 和模式的速查，覆盖搭建、事件、Hook、消息、API、Mixin、多平台、插件结构、排错。

### 复杂问题 → 读项目文档 docs/

1. **`docs/docs/notes/guide/README.md`** — 全局入口，含 Quick Start 和指南索引
2. **按需深入**：

| 关键词 | 直接查阅 |
|--------|----------|
| 快速开始/安装 | `docs/docs/notes/guide/1. 快速开始/` |
| 适配器/平台登录 | `docs/docs/notes/guide/2. 适配器/` |
| 插件/事件/Hook/生命周期 | `docs/docs/notes/guide/3. 插件开发/` |
| 消息段/转发 | `docs/docs/notes/guide/4. 消息发送/` |
| Bot API/群管理 | `docs/docs/notes/guide/5. API 使用/` |
| 配置 | `docs/docs/notes/guide/6. 配置管理/` |
| RBAC/权限 | `docs/docs/notes/guide/7. RBAC 权限/` |
| CLI | `docs/docs/notes/guide/8. 命令行工具/` |
| 测试 | `docs/docs/notes/guide/9. 测试指南/` |
| 多平台 | `docs/docs/notes/guide/10. 多平台开发/` |
| 架构/概念 | `docs/docs/notes/guide/11. 架构与概念/` |

3. **`docs/docs/notes/reference/`** — API 签名完整参考（10 个模块）
4. **`docs/docs/README.md`** — 文档全局目录树

### 框架内部问题 → codebase-nav

当需要理解框架内部实现（而非使用层面），使用 **codebase-nav** 技能。
