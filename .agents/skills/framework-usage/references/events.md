# 事件系统参考

> 参考文档：[guide/plugin/4a.event-registration.md](docs/guide/plugin/4a.event-registration.md), [reference/core/1_internals.md](docs/reference/core/1_internals.md)

## 装饰器注册（最常用）

```python
from ncatbot.core import registrar
from ncatbot.event import GroupMessageEvent, PrivateMessageEvent
```python

### 完整装饰器列表

| 装饰器 | 匹配事件 |
|--------|---------|
| `@registrar.on(event_type, priority=0)` | 任意事件 |
| `@registrar.on_message()` | 所有消息 |
| `@registrar.on_group_message()` | 群消息 |
| `@registrar.on_private_message()` | 私聊消息 |
| `@registrar.on_message_sent()` | Bot 发出的消息 |
| `@registrar.on_command(*names)` | 命令（群+私聊） |
| `@registrar.on_group_command(*names)` | 群命令 |
| `@registrar.on_private_command(*names)` | 私聊命令 |
| `@registrar.on_notice()` | 所有通知 |
| `@registrar.on_group_increase()` | 群成员增加 |
| `@registrar.on_group_decrease()` | 群成员减少 |
| `@registrar.on_poke()` | 戳一戳 |
| `@registrar.on_request()` | 所有请求 |
| `@registrar.on_friend_request()` | 好友请求 |
| `@registrar.on_group_request()` | 群请求 |
| `@registrar.on_meta()` | 元事件 |

## 事件流（EventStream）

适用于后台持续监听事件。

```python
import asyncio

async def on_load(self):
    self._task = asyncio.create_task(self._monitor())

async def on_close(self):
    if self._task:
        self._task.cancel()

async def _monitor(self):
    async with self.events("message.group") as stream:
        async for event in stream:
            if "敏感词" in event.data.message.text:
                await self.api.delete_msg(event.data.message_id)
```python

**events() 参数**：
- `None` — 接收全部事件
- `"message"` — 前缀匹配 `"message"` 及所有子类型
- `"message.group"` — 精确匹配

## 一次性等待（wait_event）

适用于多步对话。

```python
from ncatbot.core import from_event, msg_equals

@registrar.on_group_command("confirm")
async def on_confirm(self, event: GroupMessageEvent):
    await event.reply("请输入确认密码：")
    try:
        reply = await self.wait_event(
            predicate=from_event(event) * msg_equals("yes"),
            timeout=30.0,
        )
        await event.reply("已确认")
    except asyncio.TimeoutError:
        await event.reply("超时，已取消")
```python

### Predicate DSL

`ncatbot.core` 提供可组合的 Predicate DSL，用运算符替代冗长的 lambda。

**运算符**

| 运算符 | 含义 |
|--------|------|
| `p1 * p2` 或 `p1 & p2` | AND |
| `p1 + p2` 或 `p1 \| p2` | OR |
| `~p` | NOT |

**工厂函数**

| 函数 | 说明 |
|------|------|
| `from_event(event)` | 核心语法糖：自动推导同 session（同 user + 群消息同群 / 私聊同私聊） |
| `same_user(uid)` | 匹配 user_id |
| `same_group(gid)` | 匹配 group_id |
| `is_group()` / `is_private()` / `is_message()` | 匹配事件类型 |
| `msg_equals(text)` | raw_message.strip() 完全匹配 |
| `msg_in(*options)` | raw_message.strip() 匹配选项之一 |
| `has_keyword(*words)` | raw_message 含任一关键词 |
| `msg_matches(pattern)` | raw_message 正则匹配 |
| `event_type(prefix)` | event.type 前缀匹配 |
| `P.of(lambda)` | 将普通 callable 升级为可组合的 P |

**组合示例**

```python
from ncatbot.core import from_event, msg_in, has_keyword, same_user, P

# 等“确认”或“取消”
pred = from_event(event) * msg_in("确认", "取消")

# 含关键词
pred = from_event(event) * has_keyword("帮助", "help")

# 排除某用户
pred = from_event(event) * ~same_user(bot_id)

# 混用 lambda
pred = from_event(event) * P.of(lambda e: int(e.data.raw_message) > 0)
```python

## 事件类型字符串完整列表

| 事件类型 | 说明 | 数据类 |
|---------|------|--------|
| `"message.private"` | 私聊消息 | `PrivateMessageEventData` |
| `"message.group"` | 群消息 | `GroupMessageEventData` |
| `"message_sent.private"` | 私聊已发送 | — |
| `"message_sent.group"` | 群消息已发送 | — |
| `"notice.group_upload"` | 群文件上传 | `GroupUploadNoticeEventData` |
| `"notice.group_admin"` | 群管理员变更 | `GroupAdminNoticeEventData` |
| `"notice.group_decrease"` | 群成员减少 | `GroupDecreaseNoticeEventData` |
| `"notice.group_increase"` | 群成员增加 | `GroupIncreaseNoticeEventData` |
| `"notice.group_ban"` | 群禁言 | `GroupBanNoticeEventData` |
| `"notice.friend_add"` | 好友已添加 | `FriendAddNoticeEventData` |
| `"notice.group_recall"` | 群消息撤回 | `GroupRecallNoticeEventData` |
| `"notice.friend_recall"` | 好友消息撤回 | `FriendRecallNoticeEventData` |
| `"notice.poke"` | 戳一戳 | `PokeNotifyEventData` |
| `"notice.lucky_king"` | 幸运王 | `LuckyKingNotifyEventData` |
| `"notice.honor"` | 群荣誉 | `HonorNotifyEventData` |
| `"request.friend"` | 好友请求 | `FriendRequestEventData` |
| `"request.group"` | 群请求 | `GroupRequestEventData` |
| `"meta_event.lifecycle"` | 生命周期 | `LifecycleMetaEventData` |
| `"meta_event.heartbeat"` | 心跳 | `HeartbeatMetaEventData` |
| `"meta_event.heartbeat_timeout"` | 心跳超时 | `HeartbeatTimeoutMetaEventData` |

## 前缀匹配规则

```json
"message"        → 匹配 "message" + "message.group" + "message.private"
"notice"         → 匹配 "notice" + "notice.group_increase" + ...
"notice.group"   → 匹配 "notice.group_increase" + "notice.group_decrease" + ...
```python

## 事件实体层

| 实体类 | 便捷方法 |
|--------|---------|
| `MessageEvent` | `reply()`, `delete()`, `is_group_msg()` |
| `PrivateMessageEvent` | 继承 MessageEvent |
| `GroupMessageEvent` | `reply()`, `delete()`, `kick()`, `ban()` |
| `NoticeEvent` | — |
| `GroupIncreaseEvent` | `kick()` |
| `RequestEvent` | `approve()`, `reject()` |
| `FriendRequestEvent` | `approve()`, `reject()` |
| `GroupRequestEvent` | `approve()`, `reject()` |

**属性代理**（`__getattr__` 透传到 data）：

```python
event.user_id        # → event.data.user_id
event.group_id       # → event.data.group_id
event.message        # → event.data.message (MessageArray)
event.message_id     # → event.data.message_id
event.sender         # → event.data.sender
```python

## 多步对话模板

```python
from ncatbot.core import from_event, msg_in

@registrar.on_group_command("order")
async def order_flow(self, event: GroupMessageEvent):
    await event.reply("请选择: 1. 咖啡 2. 茶")
    try:
        choice_event = await self.wait_event(predicate=from_event(event), timeout=30.0)
        choice = choice_event.data.raw_message.strip()
        if choice not in ("1", "2"):
            await event.reply("无效选择，已取消")
            return
        item = "咖啡" if choice == "1" else "茶"

        await event.reply(f"确认点 {item} 吗？回复 yes/no")
        confirm_event = await self.wait_event(
            predicate=from_event(event) * msg_in("yes", "no"),
            timeout=30.0,
        )
        if confirm_event.data.raw_message.strip().lower() == "yes":
            await event.reply(f"已下单: {item}")
        else:
            await event.reply("已取消")
    except asyncio.TimeoutError:
        await event.reply("超时，已取消")
```text
