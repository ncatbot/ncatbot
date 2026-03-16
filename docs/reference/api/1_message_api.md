# 消息 API — 核心方法与便捷方法

> 核心消息方法与 MessageSugarMixin 便捷方法的完整参数表、返回值和示例。

---

## 核心消息方法

### send_group_msg()

```python
async def send_group_msg(
    self, group_id: Union[str, int], message: list, **kwargs
) -> SendMessageResult:
```python

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| group_id | str \| int | 是 | 目标群号 |
| message | list | 是 | 消息段列表（OneBot v11 格式） |

**返回值**：`SendMessageResult` — 包含 `message_id: str`

### send_private_msg()

```python
async def send_private_msg(
    self, user_id: Union[str, int], message: list, **kwargs
) -> SendMessageResult:
```python

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| user_id | str \| int | 是 | 目标用户 QQ 号 |
| message | list | 是 | 消息段列表 |

### delete_msg()

```python
async def delete_msg(self, message_id: Union[str, int]) -> None:
```python

撤回消息。**OneBot v11 Action**：`delete_msg`

### send_forward_msg()

```python
async def send_forward_msg(
    self, message_type: str, target_id: Union[str, int],
    messages: list, **kwargs,
) -> SendMessageResult:
```python

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| message_type | str | 是 | `"group"` 或 `"private"` |
| target_id | str \| int | 是 | 目标群号或用户 QQ 号 |
| messages | list | 是 | 合并转发消息节点列表 |

### send_poke()

```python
async def send_poke(
    self, group_id: Union[str, int], user_id: Union[str, int],
) -> None:
```python

戳一戳（NapCat 扩展）。

---

## MessageSugarMixin 便捷方法

> 源码：`ncatbot/api/_sugar.py`

### post_group_msg()

```python
async def post_group_msg(
    self, group_id, text=None, at=None, reply=None, image=None, video=None, rtf=None,
) -> SendMessageResult:
```python

**便捷群消息** — 组装顺序：reply → at → text → image → video → rtf。

| 参数 | 类型 | 说明 |
|---|---|---|
| text | str \| None | 文本内容 |
| at | str \| int \| None | 要 @ 的用户 QQ 号 |
| reply | str \| int \| None | 要回复的消息 ID |
| image | str \| Image \| None | 图片路径/URL |
| video | str \| Video \| None | 视频路径/URL |
| rtf | MessageArray \| None | 自定义富文本消息数组 |

### post_private_msg()

用法与 `post_group_msg` 类似，但无 `at` 参数。

### post_group_array_msg() / post_private_array_msg()

```python
async def post_group_array_msg(self, group_id, msg: MessageArray) -> SendMessageResult:
async def post_private_array_msg(self, user_id, msg: MessageArray) -> SendMessageResult:
```python

---

## 群消息 Sugar

| 方法 | 签名 | 说明 |
|------|------|------|
| `send_group_text` | `(group_id, text)` | 群纯文本 |
| `send_group_plain_text` | `(group_id, text)` | PlainText 段群文本 |
| `send_group_image` | `(group_id, image)` | 群图片 |
| `send_group_record` | `(group_id, file)` | 群语音 |
| `send_group_file` | `(group_id, file, name=None)` | 群文件 |
| `send_group_video` | `(group_id, video)` | 群视频 |
| `send_group_sticker` | `(group_id, image)` | 群动画表情 |

## 私聊消息 Sugar

| 方法 | 签名 | 说明 |
|------|------|------|
| `send_private_text` | `(user_id, text)` | 私聊纯文本 |
| `send_private_plain_text` | `(user_id, text)` | PlainText 段私聊文本 |
| `send_private_image` | `(user_id, image)` | 私聊图片 |
| `send_private_record` | `(user_id, file)` | 私聊语音 |
| `send_private_file` | `(user_id, file, name=None)` | 私聊文件 |
| `send_private_video` | `(user_id, video)` | 私聊视频 |
| `send_private_sticker` | `(user_id, image)` | 私聊动画表情 |
| `send_private_dice` | `(user_id, value=1)` | 骰子魔法表情 |
| `send_private_rps` | `(user_id, value=1)` | 猜拳魔法表情 |

## 合并转发 Sugar

| 方法 | 签名 | 说明 |
|------|------|------|
| `post_group_forward_msg` | `(group_id, forward: Forward)` | 群合并转发 |
| `post_private_forward_msg` | `(user_id, forward: Forward)` | 私聊合并转发 |
| `send_group_forward_msg_by_id` | `(group_id, message_ids: List)` | 通过消息 ID 逐条转发 |

所有方法返回 `SendMessageResult`（含 `message_id`）。
