# 实战示例

> 14 个完整场景，展示如何在插件中构造和发送各种消息。代码对齐 `examples/` 目录下的示例插件。

---

## 目录

- [发送纯文本](#发送纯文本)
- [event.reply() 快速回复](#eventreply-快速回复)
- [发送图文混排](#发送图文混排)
- [发送 URL 图片](#发送-url-图片)
- [发送视频](#发送视频)
- [发送文件](#发送文件)
- [发送动画表情](#发送动画表情)
- [回复消息（引用）](#回复消息引用)
- [合并转发消息](#合并转发消息)
- [嵌套合并转发](#嵌套合并转发)
- [从消息中提取图片](#从消息中提取图片)
- [@全体成员 并发送提示](#全体成员-并发送提示)
- [发送音乐卡片](#发送音乐卡片)
- [戳一戳](#戳一戳)

---

## 发送纯文本

> 参考 `examples/01_hello_world/main.py`

```python
from ncatbot.core.registry import registrar
from ncatbot.event import GroupMessageEvent

@registrar.on_group_command("hello", ignore_case=True)
async def on_hello(self, event: GroupMessageEvent):
    await self.api.post_group_msg(event.group_id, text="Hello, World! 👋")
```

---

## event.reply() 快速回复

> 参考 `examples/01_hello_world/main.py`

```python
@registrar.on_group_command("hi", ignore_case=True)
async def on_hi(self, event: GroupMessageEvent):
    """自动引用 + @发送者 + 文字"""
    await event.reply(text="你好呀！这是通过 event.reply() 发送的富文本快速回复 🎉")
```

---

## 发送图文混排

> 参考 `examples/03_message_types/main.py`

```python
from ncatbot.types import MessageArray

@registrar.on_group_command("图文")
async def on_rich_text(self, event: GroupMessageEvent):
    msg = MessageArray()
    msg.add_text("📸 这是一条图文混排消息:\n")
    msg.add_image(str(EXAMPLE_IMAGE))
    msg.add_text("\n以上是示例图片！")

    await self.api.post_group_array_msg(event.group_id, msg)
```

---

## 发送 URL 图片

> 参考 `examples/03_message_types/main.py`

```python
@registrar.on_group_command("图片")
async def on_image_url(self, event: GroupMessageEvent):
    msg = MessageArray()
    msg.add_text("📸 这是一条包含 URL 图片的消息:\n")
    msg.add_image("https://example.com/photo.jpg")

    await self.api.post_group_array_msg(event.group_id, msg)
```

---

## 发送视频

> 参考 `examples/03_message_types/main.py`

```python
@registrar.on_group_command("视频")
async def on_video(self, event: GroupMessageEvent):
    await self.api.post_group_msg(event.group_id, video=str(EXAMPLE_VIDEO))
```

---

## 发送文件

> 参考 `examples/03_message_types/main.py`、`examples/05_bot_api/main.py`

```python
@registrar.on_group_command("文件视频")
async def on_file_video(self, event: GroupMessageEvent):
    await self.api.send_group_file(event.group_id, str(EXAMPLE_VIDEO), name="示例视频.mp4")

@registrar.on_group_command("发文件")
async def on_send_file(self, event: GroupMessageEvent):
    await self.api.send_group_file(event.group_id, str(EXAMPLE_FILE), name="example.pdf")
```

---

## 发送动画表情

> 参考 `examples/03_message_types/main.py`

```python
@registrar.on_group_command("表情")
async def on_sticker(self, event: GroupMessageEvent):
    await self.api.send_group_sticker(event.group_id, str(EXAMPLE_IMAGE))
```

---

## 回复消息（引用）

两种方式实现引用回复：

```python
# 方式一：event.reply()（推荐，自动引用 + @）
await event.reply(text="收到！")

# 方式二：post_group_msg 的 reply 参数
await self.api.post_group_msg(
    event.group_id,
    text="收到！",
    reply=event.message_id,
)

# 方式三：手动构造 MessageArray
msg = (
    MessageArray()
    .add_reply(event.message_id)
    .add_text("收到！")
)
await self.api.post_group_array_msg(event.group_id, msg)
```

---

## 合并转发消息

> 参考 `examples/03_message_types/main.py`

```python
from ncatbot.types import ForwardConstructor, MessageArray

@registrar.on_group_command("转发")
async def on_forward(self, event: GroupMessageEvent):
    fc = ForwardConstructor(user_id=str(event.self_id), nickname="Bot")

    fc.attach_text("这是转发消息的第一条 📝")
    fc.attach_text("这是转发消息的第二条 📝")

    # 图文混合节点
    msg = MessageArray()
    msg.add_text("这条包含图片: ")
    msg.add_image(str(EXAMPLE_IMAGE))
    fc.attach_message(msg)

    forward = fc.build()
    await self.api.post_group_forward_msg(event.group_id, forward)
```

---

## 嵌套合并转发

> 参考 `examples/03_message_types/main.py`

```python
@registrar.on_group_command("嵌套转发")
async def on_nested_forward(self, event: GroupMessageEvent):
    bot_id = str(event.self_id)

    # 构造内层转发
    inner_fc = ForwardConstructor(user_id=bot_id, nickname="Bot 内层")
    inner_fc.attach_text("🔹 内层第一条消息")
    inner_fc.attach_text("🔹 内层第二条消息")
    inner_forward = inner_fc.build()

    # 构造外层转发，嵌套内层
    outer_fc = ForwardConstructor(user_id=bot_id, nickname="Bot")
    outer_fc.attach_text("🔸 外层第一条消息")
    outer_fc.attach_forward(inner_forward)
    outer_fc.attach_text("🔸 外层第三条消息（在嵌套转发之后）")

    forward = outer_fc.build()
    await self.api.post_group_forward_msg(event.group_id, forward)
```

---

## 从消息中提取图片

> 参考 `examples/03_message_types/main.py`

```python
from ncatbot.types import Image

@registrar.on_group_message()
async def on_extract_image(self, event: GroupMessageEvent):
    images = event.message.filter(Image)
    if not images:
        return

    lines = [f"🖼️ 检测到 {len(images)} 张图片:"]
    for i, img in enumerate(images, 1):
        url = getattr(img, "url", None) or getattr(img, "file", "未知")
        lines.append(f"  图片 {i}: {url}")

    await event.reply("\n".join(lines))
```

---

## @全体成员 并发送提示

```python
from ncatbot.types import MessageArray

@registrar.on_group_command("通知")
async def on_notify(self, event: GroupMessageEvent):
    msg = (
        MessageArray()
        .add_at_all()
        .add_text(" 重要通知：明天放假！")
    )
    await self.api.post_group_array_msg(event.group_id, msg)
```

---

## 发送音乐卡片

```python
from ncatbot.types.segment import Music, MessageArray

@registrar.on_group_command("点歌")
async def on_music(self, event: GroupMessageEvent):
    music = Music(type="qq", id="12345")
    msg = MessageArray().add_segment(music)
    await self.api.post_group_array_msg(event.group_id, msg)
```

---

## 戳一戳

> 参考 `examples/05_bot_api/main.py`

```python
@registrar.on_group_command("戳我")
async def on_poke(self, event: GroupMessageEvent):
    await self.api.send_poke(event.group_id, event.user_id)
```

---

[← 上一篇：便捷接口参考](5_sugar.md) | [返回目录](README.md)
