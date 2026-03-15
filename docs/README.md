# NcatBot 文档索引

## 🏗️ 架构

- [架构总览](architecture.md) — 项目整体架构、模块职责、数据流与生命周期

## 📖 用户指南

- [插件开发指南](guide/plugin/) — 从入门到实战的完整插件开发文档
  - [1. 快速入门](guide/plugin/1.quick-start.md) — 5 分钟跑通第一个插件
  - [2. 插件结构](guide/plugin/2.structure.md) — manifest.toml、目录布局、基类选择
  - [3. 生命周期](guide/plugin/3.lifecycle.md) — 插件加载/卸载流程、Mixin 钩子链
  - [4. 事件处理](guide/plugin/4.event-handling.md) — 三种事件消费模式
  - [5. Mixin 能力体系](guide/plugin/5.mixins.md) — 配置、数据、权限、定时任务
  - [6. Hook 机制](guide/plugin/6.hooks.md) — 中间件、过滤器、参数绑定
  - [7. 高级主题](guide/plugin/7.advanced.md) — 热重载、依赖管理、多步对话
- [消息类型详解](guide/send_message/) — 消息段构造、MessageArray、合并转发
- [发送消息指南](guide/send_message/README.md) — 消息构造、便捷接口、发送文件、合并转发等
