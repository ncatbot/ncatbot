# 快速上手：发送消息

> 三种方式，从简到灵活，覆盖日常 90% 的发送需求。

---

## 目录

- [方式一：event.reply() — 最快回复](#方式一eventreply--最快回复)
- [方式二：post_group_msg — 关键字快捷发送](#方式二post_group_msg--关键字快捷发送)
- [方式三：MessageArray — 自由组装](#方式三messagearray--自由组装)

---

## 方式一：event.reply() — 最快回复

在事件处理器中，`event.reply()` 是最便捷的回复方式：自动引用原消息并 @发送者。

```python
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent

@registrar.on_group_command("hello", ignore_case=True)
async def on_hello(self, event: GroupMessageEvent):
    await event.reply(text="你好呀！🎉")
```

**签名：**

```python
async def reply(
    self,
    text: str | None = None,
    *,
    at: str | int | None = None,       # 额外 @某人
    image: str | Image | None = None,   # 附带图片
    video: str | Video | None = None,   # 附带视频
    rtf: MessageArray | None = None,    # 附带自定义 MessageArray
    at_sender: bool = True,             # 是否自动 @发送者（群聊默认 True）
) -> Any
```

**行为：**
- 自动添加 `Reply`（引用原消息）
- 群聊时自动 `@发送者`（可通过 `at_sender=False` 关闭）
- 私聊时只引用不 @

```python
# 回复图片
await event.reply(image="https://example.com/img.png")

# 回复文字 + 图片
await event.reply(text="看这张图", image="/path/to/img.png")

# 不 @发送者
await event.reply(text="收到", at_sender=False)

# 附带自定义 MessageArray
msg = MessageArray().add_text("复杂消息 ").add_image("a.png")
await event.reply(rtf=msg)
```

---

## 方式二：post_group_msg — 关键字快捷发送

不需要引用回复时，使用 `self.api.post_group_msg()`，通过关键字参数快捷组装消息：

```python
@registrar.on_group_command("hello")
async def on_hello(self, event: GroupMessageEvent):
    await self.api.post_group_msg(event.group_id, text="Hello, World! 👋")
```

**签名：**

```python
async def post_group_msg(
    self,
    group_id: str | int,
    text: str | None = None,
    at: str | int | None = None,
    reply: str | int | None = None,     # 消息 ID
    image: str | Image | None = None,
    video: str | Video | None = None,
    rtf: MessageArray | None = None,
) -> dict
```

**参数组装顺序：** `reply → at → text → image → video → rtf`

```python
# 纯文本
await self.api.post_group_msg(gid, text="你好！")

# 文字 + 图片
await self.api.post_group_msg(gid, text="📸 看图:", image=str(EXAMPLE_IMAGE))

# @某人 + 文字
await self.api.post_group_msg(gid, text=" 欢迎！", at=event.user_id)

# 引用回复 + 文字
await self.api.post_group_msg(gid, text="已收到", reply=event.message_id)

# 发视频
await self.api.post_group_msg(gid, video=str(video_path))
```

> 私聊版本为 `post_private_msg(user_id, ...)`，参数相同（无 `at` 参数）。

---

## 方式三：MessageArray — 自由组装

需要更复杂的消息内容时，使用 `MessageArray` 链式构造：

```python
from ncatbot.types import MessageArray

msg = (
    MessageArray()
    .add_at(event.user_id)
    .add_text(" 你好！看看这张图 ")
    .add_image("https://example.com/img.png")
)
await self.api.post_group_array_msg(event.group_id, msg)
```

也可以通过 `rtf` 参数传入 `post_group_msg`：

```python
msg = (
    MessageArray()
    .add_reply(event.message_id)
    .add_text("自定义排列 ")
    .add_image("https://example.com/1.png")
    .add_image("https://example.com/2.png")
)
await self.api.post_group_msg(event.group_id, rtf=msg)
```

> 详见 [3_array.md — MessageArray 消息数组](3_array.md)

---

## 下一步

- 了解所有消息段类型 → [2_segments.md](2_segments.md)
- 精通 MessageArray → [3_array.md](3_array.md)
- 发送合并转发 → [4_forward.md](4_forward.md)
- 查看全部便捷接口 → [5_sugar.md](5_sugar.md)
- 看完整示例 → [6_examples.md](6_examples.md)

---

[返回目录](README.md) | [下一篇：消息段参考 →](2_segments.md)
