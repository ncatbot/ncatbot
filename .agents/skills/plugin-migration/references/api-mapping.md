# API 变更映射

## 1. 命令与事件注册

### 4.4 → 5.0

| 4.4 方式 | 5.0 等价 | 说明 |
|---------|---------|------|
| `self.register_user_func(name="cmd", handler=fn, prefix="/cmd")` | `@registrar.on_command("cmd")` 装饰器 | 移除命令式注册，改用装饰器 |
| `self.register_admin_func(name="cmd", handler=fn, prefix="/cmd")` | `@registrar.on_command("cmd")` + RBACMixin 权限检查 | admin 过滤改为 RBAC |
| `self.register_handler("ncatbot.group_message_event", handler)` | `@registrar.on_group_message()` 或 `@registrar.on("message")` | |
| `self.register_handler("ncatbot.private_message_event", handler)` | `@registrar.on_private_message()` | |
| `self.register_handler("ncatbot.notice_event", handler)` | `@registrar.on_notice()` | |
| `self.register_handler("ncatbot.request_event", handler)` | `@registrar.on_request()` | |
| `self.register_handler("re:test\.", handler)` | `@registrar.on("message")` + Hook 或 handler 内判断 | 正则事件匹配需手动实现 |
| `self.event_bus.publish_async(Event("type", data))` | 5.0 无直接等价，可用 service 层实现跨插件通信 | 见注 |
| `self.event_bus.unregister_handler(hid)` | 自动管理，无需手动取消 | handler 随插件卸载自动清理 |
| `self.unregister_all_handler()` | 无需调用 | 插件卸载时自动清理 |
| `@command_registry.command("cmd")` | `@registrar.on_command("cmd")` | 装饰器名不同 |
| `@filter_registry.group_filter` | `@registrar.on_group_message()` 或 `@registrar.on_group_command()` | 内置到 registrar |
| `@filter_registry.private_filter` | `@registrar.on_private_message()` 或 `@registrar.on_private_command()` | |
| `@admin_filter` | Handler 内使用 `self.check_permission(event.user_id, "path")` | RBAC 替代 |
| `@group_filter` | `@registrar.on_group_command()` / `@registrar.on_group_message()` | |
| `@CustomFilter(lambda e: ...)` | `@add_hooks(hook)` 或 handler 内 if 判断 | Hook 系统替代 |
| `@option(short_name="v", long_name="verbose")` | 5.0 通过函数签名自动解析参数 | 类型注解替代显式声明 |

### 4.5 → 5.0

| 4.5 方式 | 5.0 等价 | 说明 |
|---------|---------|------|
| 方法名即命令名（隐式注册） | `@registrar.on_command("method_name")` | **必须**显式添加装饰器 |

### 5.0 registrar 装饰器速查

```python
from ncatbot.core import registrar

# 命令（最常用）
@registrar.on_command("cmd")                    # 所有消息类型
@registrar.on_command("cmd1", "cmd2")           # 多个命令名
@registrar.on_group_command("cmd")              # 仅群消息
@registrar.on_private_command("cmd")            # 仅私聊

# 消息（无命令匹配，接收所有消息）
@registrar.on_message()                         # 所有消息
@registrar.on_group_message()                   # 仅群消息
@registrar.on_private_message()                 # 仅私聊

# 通知/请求
@registrar.on_notice()                          # 所有通知
@registrar.on_request()                         # 所有请求
@registrar.on_group_increase()                  # 群成员增加
@registrar.on_friend_request()                  # 好友请求

# 通用
@registrar.on(event_type, priority=0)           # 监听任意事件类型
```

---

## 2. Config API

| 4.4/4.5 方式 | 5.0 等价 | 说明 |
|-------------|---------|------|
| `self.register_config("key", default, description=..., value_type=..., metadata=...)` | `if self.get_config("key") is None: self.set_config("key", default)` | register_config 不存在于 5.0 |
| `self.config["key"]` | `self.get_config("key")` 或 `self.config["key"]` | 两者皆可，推荐 get_config |
| `self.data['config']['key']` | `self.get_config("key")` | 4.5 data 嵌套 config，5.0 分离 |
| `on_change_xxx` 配置回调 | 无等价 | 5.0 无配置变更回调 |
| `/set_config plugin key value` 用户命令 | 视具体实现 | 5.0 需自行实现 |

### 5.0 ConfigMixin 完整 API

```python
# 在 on_load() 中初始化
async def on_load(self):
    if self.get_config("key") is None:
        self.set_config("key", "default_value")

# 读取
val = self.get_config("key")
val = self.get_config("key", default="fallback")

# 写入（立即持久化到 config.yaml）
self.set_config("key", "new_value")

# 删除
self.remove_config("key")

# 批量更新
self.update_config({"k1": "v1", "k2": "v2"})
```

---

## 3. 数据持久化

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `self.data` 无标准接口 | `self.data` 字典（DataMixin） | 5.0 新增，自动持久化到 data.json |

### 5.0 DataMixin 用法

```python
async def on_load(self):
    self.data.setdefault("counter", 0)    # 用 setdefault 避免覆盖

self.data["counter"] += 1                 # 直接操作
self._save_data()                         # 手动持久化（通常不需要，卸载时自动保存）
```

---

## 4. 消息段构造

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `Image(path)` | `Image(file=path)` | **Pydantic model，必须关键字参数** |
| `Image(file="url")` | `Image(file="url")` | 不变 |
| `Text("hello")` | `PlainText("hello")` 或 `MessageArray().add_text("hello")` | 类名变更 |
| `At("123")` | `At(qq="123")` | 确认是否需要关键字参数 |
| `Record(file="path")` | `Record(file="path")` | 不变 |
| `Video(file="path")` | `Video(file="path")` | 不变 |
| `Node(user_id, nickname, content)` | `ForwardNode(...)` | 类名变更 |
| `Message().append(segment)` | `MessageArray().add_text(...)` 链式构造 | Message → MessageArray |
| `MessageArray(seg1, seg2, ...)` | `MessageArray(seg1, seg2, ...)` | 不变 |
| `MessageArray(generator)` | `MessageArray(generator)` | 不变 |

### 5.0 消息构造模式

```python
from ncatbot.types import MessageArray, Image, PlainText, At

# 链式构造
msg = MessageArray().add_text("Hello ").add_at(user_id).add_image("pic.jpg")

# 直接构造
msg = MessageArray(PlainText("Hello"), Image(file="pic.jpg"))

# 生成器
msg = MessageArray(Image(file=path) for path in image_paths)
```

---

## 5. 事件类型

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `BaseMessageEvent` | `MessageEvent` | 名称变更 |
| `GroupMessageEvent` | `GroupMessageEvent` | 不变 |
| `PrivateMessageEvent` | `PrivateMessageEvent` | 不变 |
| `RequestEvent` | `RequestEvent` | 不变 |
| `NoticeEvent` | `NoticeEvent` | 不变 |
| `event.post_type` | `event.post_type` | 不变 |
| `event.message_type` | `event.message_type` | 不变 |
| `event.is_group_event()` | `isinstance(event, GroupMessageEvent)` | 方法 → isinstance |
| `hasattr(event, "group_id")` | `isinstance(event, GroupMessageEvent)` | 推荐 isinstance |

### 事件属性（不变）

```python
# 通用
event.message_id    # str
event.user_id       # str
event.raw_message   # str
event.sender        # BaseSender / GroupSender
event.self_id       # Bot QQ

# GroupMessageEvent
event.group_id      # str

# reply 方法
await event.reply(text="Hello")
await event.reply(rtf=msg_array)
await event.reply(text="看图", image="url")
```

---

## 6. BotAPI 方法

大部分 BotAPI 方法名称不变：

```python
# 以下方法在 4.4/4.5 和 5.0 中签名一致
await self.api.post_group_msg(group_id, text=..., at=..., reply=..., image=..., rtf=...)
await self.api.post_private_msg(user_id, text=..., image=...)
await self.api.post_group_forward_msg(group_id=..., forward=...)
await self.api.post_private_forward_msg(user_id=..., forward=...)
await self.api.post_group_array_msg(group_id, msg_array)
await self.api.send_group_text(group_id, text)
await self.api.send_group_image(group_id, image)
```

### ForwardConstructor（不变）

```python
from ncatbot.types import ForwardConstructor  # 仅导入路径变更

fcr = ForwardConstructor(self_id, "昵称")
fcr.attach_image(image_path)
fcr.attach_text("文本")
forward = fcr.to_forward()
await self.api.post_group_forward_msg(group_id=gid, forward=forward)
```

---

## 7. 定时任务

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `self.add_scheduled_task(job_func, name, interval, ...)` | `self.add_scheduled_task(job_func, name, interval, ...)` | 接口基本一致 |
| `conditions=[fn]` | `conditions=[fn]` | 不变 |
| `max_runs=N` | `max_runs=N` | 不变 |
| 时间格式 `"1h"` / `"09:30"` / `"2025-12-31"` | 同上 | 不变 |

---

## 8. RBAC 权限

| 4.4/4.5 | 5.0 | 说明 |
|---------|-----|------|
| `self.rbac_manager.check_permission(uid, path)` | `self.check_permission(uid, path)` | 直接调用 Mixin 方法 |
| `self.rbac_manager.assign_permissions_to_user(...)` | `self.add_permission(path)` 注册 + RBAC service 管理 | 简化 API |
| `self.rbac_manager.assign_role_to_user(uid, role)` | 通过 RBAC service 管理 | |

---

## 9. 其它变更

| 项目 | 4.4/4.5 | 5.0 |
|------|---------|-----|
| 参数命名惯例 | `msg: MessageEvent` | `event: MessageEvent` |
| 日志 | `print()` 混用 | `LOG = get_log("name"); LOG.info(...)` |
| `__init__.py` 中的 `__all__` | 必需（多插件文件） | 非必需（manifest.toml 指定 entry_class）|
| `dependencies = {}` 类属性 | 必需 | 移至 manifest.toml `[dependencies]` |
| 插件间通信 | `self.event_bus.publish_async()` | 无直接等价，可通过 service 层 |
| sync API | `method_sync()` 后缀 | 不推荐，统一 async |
