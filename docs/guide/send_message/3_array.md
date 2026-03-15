# MessageArray 消息数组

> 消息段的容器，提供链式构造、查询过滤和序列化能力。

---

## 目录

- [创建 MessageArray](#创建-messagearray)
- [链式构造](#链式构造)
- [查询与过滤](#查询与过滤)
- [序列化与反序列化](#序列化与反序列化)
- [容器操作](#容器操作)

---

## 创建 MessageArray

```python
from ncatbot.types.segment import MessageArray, PlainText, At

# 方式一：直接传入消息段列表
msg = MessageArray([PlainText(text="Hello"), At(qq="123456")])

# 方式二：空数组
msg = MessageArray()

# 方式三：从 OB11 字典列表反序列化
msg = MessageArray.from_list([
    {"type": "text", "data": {"text": "Hello"}},
    {"type": "at", "data": {"qq": "123456"}},
])

# 方式四：从任意数据解析（支持字符串 CQ 码、字典、MessageSegment 等）
msg = MessageArray.from_any("[CQ:at,qq=123456]Hello")
```

---

## 链式构造

`MessageArray` 支持链式调用来逐步添加消息段，所有方法返回 `self`：

| 方法 | 参数 | 说明 |
|---|---|---|
| `add_text(text)` | `text: str` | 添加纯文本（支持 CQ 码自动解析） |
| `add_image(image)` | `image: str \| Image` | 添加图片 |
| `add_video(video)` | `video: str \| Video` | 添加视频 |
| `add_at(user_id)` | `user_id: str \| int` | 添加 @某人 |
| `add_at_all()` | — | 添加 @全体成员 |
| `add_reply(message_id)` | `message_id: str \| int` | 添加回复引用 |
| `add_segment(segment)` | `segment: MessageSegment` | 添加任意消息段 |
| `add_segments(data)` | `data: Any` | 添加任意数据（自动解析） |

```python
from ncatbot.types.segment import MessageArray

msg = (
    MessageArray()
    .add_reply(12345)                              # 回复引用
    .add_at(123456)                                # @某人
    .add_text(" 你好！看看这张图 ")                   # 文本
    .add_image("https://example.com/img.png")       # 图片
    .add_video("https://example.com/video.mp4")     # 视频
)
```

---

## 查询与过滤

`MessageArray` 提供多种查询方法来提取特定类型的消息段：

| 方法 | 返回值 | 说明 |
|---|---|---|
| `filter()` | `List[MessageSegment]` | 返回所有消息段 |
| `filter(cls)` | `List[T]` | 返回指定类型的消息段 |
| `filter_text()` | `List[PlainText]` | 过滤纯文本段 |
| `filter_at()` | `List[At]` | 过滤 @段 |
| `filter_image()` | `List[Image]` | 过滤图片段 |
| `filter_video()` | `List[Video]` | 过滤视频段 |
| `filter_face()` | `List[Face]` | 过滤表情段 |
| `text` | `str`（属性） | 拼接所有纯文本段的文本内容 |
| `is_at(user_id)` | `bool` | 是否 @了指定用户（`"all"` 也算） |
| `is_forward_msg()` | `bool` | 是否包含合并转发 |

```python
from ncatbot.types.segment import MessageArray, Image

msg = MessageArray.from_list([
    {"type": "at", "data": {"qq": "123456"}},
    {"type": "text", "data": {"text": " 看这张图 "}},
    {"type": "image", "data": {"file": "https://example.com/img.png"}},
])

texts = msg.filter_text()        # [PlainText(text=' 看这张图 ')]
print(msg.text)                  # " 看这张图 "
images = msg.filter_image()      # [Image(file='https://...')]
msg.is_at(123456)                # True
msg.is_at(999999)                # False

# 按类型泛型过滤
from ncatbot.types.segment import Record
records = msg.filter(Record)     # []
```

---

## 序列化与反序列化

```python
from ncatbot.types.segment import MessageArray, PlainText, At

# 序列化为 OB11 字典列表
msg = MessageArray([PlainText(text="Hello"), At(qq="123456")])
data = msg.to_list()
# [{"type": "text", "data": {"text": "Hello"}}, {"type": "at", "data": {"qq": "123456"}}]

# 从 OB11 字典列表反序列化
msg2 = MessageArray.from_list(data)

# 从任意数据（CQ 码字符串、字典、混合）
msg3 = MessageArray.from_any("[CQ:at,qq=123456]你好")
```

---

## 容器操作

`MessageArray` 支持标准容器协议：

```python
msg = MessageArray([PlainText(text="A"), PlainText(text="B")])

# 迭代
for seg in msg:
    print(seg)

# 长度
len(msg)  # 2

# 拼接（返回新 MessageArray）
msg2 = msg + [PlainText(text="C")]
msg3 = msg + MessageArray([At(qq="123")])
```

---

[← 上一篇：消息段参考](2_segments.md) | [返回目录](README.md) | [下一篇：合并转发 →](4_forward.md)
