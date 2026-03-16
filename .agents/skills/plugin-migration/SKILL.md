---
name: plugin-migration
description: '将 NcatBot 4.4/4.5 版本插件迁移到 5.0。包括导入路径、注册方式、Config/Data API、事件类型、消息构造的全面映射。Use when: 迁移插件、升级插件、4 转 5、老版本、旧版本、migration、upgrade、plugin migration、版本升级。'
license: MIT
---

# 技能指令

你是 NcatBot 插件迁移助手。帮助用户将 4.4/4.5 版本的插件迁移到 5.0 版本。

## 协作技能

| 需要做什么 | 委托给 |
|-----------|--------|
| 理解 5.0 框架用法、API | **framework-usage** |
| 定位框架内部实现细节 | **codebase-nav** |
| 验证迁移后的插件 | **testing** |
| 修改框架本体（如发现兼容问题） | **framework-dev** |

---

## 工作流

```
1. 版本识别 → 2. 代码扫描 → 3. 逐项迁移 → 4. 清单验证
```

### Step 1：版本识别

读取插件源码，根据以下特征判断来源版本：

| 特征 | 版本 |
|------|------|
| `from ncatbot.plugin_system import NcatBotPlugin, filter_registry` | 4.4 |
| `register_user_func()` / `register_admin_func()` | 4.4 |
| `register_handler("event_type", handler)` | 4.4 |
| `@command_registry.command("cmd")` | 4.4 |
| `@filter_registry.group_filter` / `@filter_registry.private_filter` | 4.4 |
| `from ncatbot.plugin_system.builtin_mixin import NcatBotPlugin` | 4.5 |
| `self.register_config("key", default, description=..., value_type=...)` | 4.5 |
| 方法名即命令名（无装饰器，方法名自动注册为命令） | 4.5 |
| `self.data['config']['key']` 嵌套访问配置 | 4.5 |
| `self.event_bus.publish_async()` | 4.4 |
| `on_change_xxx` 配置变更回调方法 | 4.5 |
| `dependencies = {}` 类属性 | 4.4 / 4.5 |

> 部分插件可能混用 4.4 和 4.5 的模式。按出现的特征逐条迁移即可。

### Step 2：代码扫描

列出插件中需要迁移的所有项目，按类别分组：

1. **导入路径** — 所有 import 语句
2. **注册方式** — 命令/事件/过滤器的注册
3. **Config API** — 配置的注册和访问
4. **消息构造** — MessageArray、Image 等消息段
5. **事件类型** — MessageEvent、GroupMessageEvent 等
6. **BotAPI 调用** — self.api.xxx()
7. **元数据** — 类属性、manifest
8. **生命周期** — on_load/on_close 中的逻辑
9. **其它** — 未归类的变更

### Step 3：逐项迁移

按照 references 中的映射表执行变更。核心原则：**一次改一类，改完立即验证**。

建议顺序：

1. **创建/更新 manifest.toml**（→ [checklist.md](./references/checklist.md)）
2. **更新全部导入路径**（→ [import-mapping.md](./references/import-mapping.md)）
3. **迁移命令/事件注册**（→ [api-mapping.md](./references/api-mapping.md) § 注册方式）
4. **迁移 Config API**（→ [api-mapping.md](./references/api-mapping.md) § Config）
5. **更新消息构造**（→ [api-mapping.md](./references/api-mapping.md) § 消息段）
6. **细化事件类型与类型判断**（→ [api-mapping.md](./references/api-mapping.md) § 事件类型）
7. **清理废弃代码**（dependencies 类属性、未使用导入、print → LOG）
8. **更新 `__init__.py`**

### Step 4：清单验证

使用 [checklist.md](./references/checklist.md) 逐项验证迁移结果。

**验证手段**：
1. `get_errors` 检查语法/类型错误
2. 编写验证脚本确认 manifest 可解析、入口类可导入、handler 已注册
3. 如有测试环境，使用 **testing** 技能运行冒烟测试

---

## 迁移实践要点

以下要点来自 Lolicon4xx 插件的实际迁移实践：

### 易错点

1. **`Image(path)` → `Image(file=path)`**：5.0 的 Image 是 Pydantic model，不接受位置参数，必须用关键字参数 `file=`。
2. **方法名隐式注册在 5.0 中不存在**：4.5 中方法名自动注册为命令的约定被完全移除，必须为每个命令方法添加 `@registrar` 装饰器。
3. **`self.data['config']['key']` ≠ `self.get_config('key')`**：4.5 中 data 结构嵌套了 config，5.0 中 config 和 data 完全分离。
4. **`on_change_xxx` 配置回调不存在于 5.0**：5.0 ConfigMixin 没有配置变更回调机制，需自行处理。
5. **`dependencies = {}` 类属性需移除**：依赖声明移至 manifest.toml 的 `[dependencies]`。
6. **name/version 类属性须与 manifest.toml 一致**：两处都要声明，且值必须相同。
7. **事件参数命名惯例**：4.5 常用 `msg`，5.0 推荐 `event`。
8. **类型判断改用 isinstance**：`hasattr(msg, "group_id")` → `isinstance(event, GroupMessageEvent)`。

### 不需要改的

1. **`self.api.post_group_forward_msg()`** — API 名称未变
2. **`ForwardConstructor` 的 `attach_image()`/`attach_text()`/`to_forward()`** — 接口未变，仅导入路径变更
3. **`MessageArray` 的生成器构造** — `MessageArray(Image(file=x) for x in imgs)` 仍有效
4. **`event.reply()` 方法** — 签名基本一致
5. **`self.api` 的使用方式** — 注入机制变化但使用方式不变

---

## 参考文件

| 文件 | 内容 |
|------|------|
| [import-mapping.md](./references/import-mapping.md) | 完整的 4.4/4.5 → 5.0 导入路径映射 |
| [api-mapping.md](./references/api-mapping.md) | 注册方式、Config、消息构造、BotAPI、事件类型的全面映射 |
| [checklist.md](./references/checklist.md) | 迁移完成后的逐项验证清单 |
