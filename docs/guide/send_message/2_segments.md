# 消息段参考

> 所有消息段类型的字段、构造方式和序列化格式。

---

## 目录

- [基类 MessageSegment](#基类-messagesegment)
- [基础消息段](#基础消息段)
  - [PlainText — 纯文本](#plaintext--纯文本)
  - [At — @某人](#at--某人)
  - [Face — QQ 表情](#face--qq-表情)
  - [Reply — 回复消息](#reply--回复消息)
- [多媒体消息段](#多媒体消息段)
  - [DownloadableSegment — 可下载资源基类](#downloadablesegment--可下载资源基类)
  - [Image — 图片](#image--图片)
  - [Record — 语音](#record--语音)
  - [Video — 视频](#video--视频)
  - [File — 文件](#file--文件)
- [富文本消息段](#富文本消息段)
  - [Share — 链接分享](#share--链接分享)
  - [Location — 定位](#location--定位)
  - [Music — 音乐](#music--音乐)
  - [Json — JSON 消息](#json--json-消息)
  - [Markdown — Markdown 消息](#markdown--markdown-消息)

---

## 基类 MessageSegment

所有消息段继承自 `MessageSegment`（Pydantic `BaseModel`）。

| 属性 / 方法 | 说明 |
|---|---|
| `_type: ClassVar[str]` | 内部判别标识，对应 OB11 外层 `type` |
| `to_dict() → Dict` | 序列化为 OB11 格式 `{"type": "...", "data": {...}}` |
| `from_dict(data) → MessageSegment` | 从 OB11 字典解析为具体子类（委托给 `parse_segment`） |

```python
from ncatbot.types.segment import PlainText

seg = PlainText(text="Hello")
print(seg.to_dict())
# {"type": "text", "data": {"text": "Hello"}}
```

`parse_segment()` 根据 `type` 字段自动查找对应子类并实例化：

```python
from ncatbot.types.segment import parse_segment

seg = parse_segment({"type": "at", "data": {"qq": "123456"}})
# 返回 At(qq='123456')
```

---

## 基础消息段

### PlainText — 纯文本

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `text` | `str` | ✅ | 文本内容 |

```python
from ncatbot.types.segment import PlainText

seg = PlainText(text="你好世界")
seg.to_dict()
# {"type": "text", "data": {"text": "你好世界"}}
```

### At — @某人

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `qq` | `str` | ✅ | QQ号（纯数字）或 `"all"` 表示 @全体成员 |

`qq` 字段会自动验证：必须为纯数字或 `"all"`，传入整数会自动转为字符串。

```python
from ncatbot.types.segment import At

seg = At(qq="123456")
seg = At(qq=123456)     # 整数自动转换
seg_all = At(qq="all")  # @全体成员
```

### Face — QQ 表情

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | `str` | ✅ | QQ 表情 ID（自动转为字符串） |

```python
from ncatbot.types.segment import Face

seg = Face(id="178")
seg = Face(id=178)      # 整数自动转换
seg.to_dict()
# {"type": "face", "data": {"id": "178"}}
```

### Reply — 回复消息

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `id` | `str` | ✅ | 被回复消息的 ID（自动转为字符串） |

```python
from ncatbot.types.segment import Reply

seg = Reply(id="12345")
seg = Reply(id=12345)   # 整数自动转换
seg.to_dict()
# {"type": "reply", "data": {"id": "12345"}}
```

---

## 多媒体消息段

### DownloadableSegment — 可下载资源基类

所有多媒体类型（Image / Record / Video / File）都继承自此基类，共享以下字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `file` | `str` | ✅ | 文件标识：URL、本地路径或 base64 编码 |
| `url` | `str?` | ❌ | 文件下载地址（收到消息时由平台填充） |
| `file_id` | `str?` | ❌ | 文件 ID |
| `file_size` | `int?` | ❌ | 文件大小（字节） |
| `file_name` | `str?` | ❌ | 文件名 |

`file` 字段支持三种格式：

| 格式 | 示例 | 说明 |
|---|---|---|
| URL | `"https://example.com/img.png"` | 远程地址 |
| 本地路径 | `"file:///C:/img.png"` | 本地文件（也可直接传绝对路径） |
| Base64 | `"base64://iVBORw0KGgo..."` | base64 编码数据 |

### Image — 图片

继承自 `DownloadableSegment`，额外字段：

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|---|---|---|---|---|
| `sub_type` | `int` | ❌ | `0` | 子类型（`1` = 动画表情） |
| `type` | `int?` | ❌ | `None` | `0` = 普通图片，`1` = 闪照 |

```python
from ncatbot.types.segment import Image

img = Image(file="https://example.com/photo.jpg")          # URL
img = Image(file="file:///C:/Users/photo.jpg")              # 本地路径
img = Image(file="base64://iVBORw0KGgoAAAANSUhEUg...")      # base64
img = Image(file="https://example.com/photo.jpg", type=1)   # 闪照
```

### Record — 语音

继承自 `DownloadableSegment`，额外字段：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `magic` | `int?` | ❌ | 是否变声（`1` 为变声） |

```python
from ncatbot.types.segment import Record

rec = Record(file="https://example.com/audio.silk")
rec = Record(file="file:///C:/voice.amr", magic=1)  # 变声
```

### Video — 视频

继承自 `DownloadableSegment`，无额外字段。

```python
from ncatbot.types.segment import Video

vid = Video(file="https://example.com/video.mp4")
```

### File — 文件

继承自 `DownloadableSegment`，无额外字段。主要通过 `file_name` 字段指定文件名。

```python
from ncatbot.types.segment import File

f = File(file="https://example.com/doc.pdf", file_name="使用手册.pdf")
```

---

## 富文本消息段

### Share — 链接分享

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `url` | `str` | ✅ | 分享链接 |
| `title` | `str` | ✅ | 分享标题 |
| `content` | `str?` | ❌ | 分享描述 |
| `image` | `str?` | ❌ | 预览图 URL |

```python
from ncatbot.types.segment import Share

seg = Share(
    url="https://github.com/ncatbot/NcatBot",
    title="NcatBot",
    content="Python QQ 机器人框架",
    image="https://example.com/preview.png",
)
```

### Location — 定位

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `lat` | `float` | ✅ | 纬度 |
| `lon` | `float` | ✅ | 经度 |
| `title` | `str?` | ❌ | 位置标题 |
| `content` | `str?` | ❌ | 位置描述 |

```python
from ncatbot.types.segment import Location

seg = Location(lat=39.9042, lon=116.4074, title="北京", content="天安门广场")
```

### Music — 音乐

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `type` | `Literal["qq", "163", "custom"]` | ✅ | 音乐平台 |
| `id` | `str?` | ❌ | 歌曲 ID（`qq` / `163` 平台） |
| `url` | `str?` | ❌ | 跳转链接（`custom` 类型） |
| `audio` | `str?` | ❌ | 音频链接（`custom` 类型） |
| `title` | `str?` | ❌ | 歌曲标题（`custom` 类型） |

> **注意**：`Music` 的 `type` 字段是 OB11 `data.type` 的原始语义，与基类 `_type = "music"` 不同。

```python
from ncatbot.types.segment import Music

seg = Music(type="qq", id="12345")        # QQ 音乐
seg = Music(type="163", id="67890")       # 网易云
seg = Music(                              # 自定义
    type="custom",
    url="https://music.example.com",
    audio="https://music.example.com/song.mp3",
    title="自定义歌曲",
)
```

### Json — JSON 消息

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `data` | `str` | ✅ | JSON 字符串内容 |

```python
from ncatbot.types.segment import Json

seg = Json(data='{"app":"com.example","desc":"卡片消息"}')
```

### Markdown — Markdown 消息

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `content` | `str` | ✅ | Markdown 内容 |

```python
from ncatbot.types.segment import Markdown

seg = Markdown(content="# 标题\n**粗体**\n- 列表项")
```

---

[← 上一篇：快速上手](1_quickstart.md) | [返回目录](README.md) | [下一篇：MessageArray →](3_array.md)
