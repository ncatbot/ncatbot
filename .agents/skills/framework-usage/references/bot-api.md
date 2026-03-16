# Bot API 完整参考

> 参考文档：[guide/api_usage/](docs/guide/api_usage/), [reference/api/](docs/reference/api/)

## 消息发送 API

### 原子方法（顶层）

```python
await self.api.send_group_msg(group_id, message=[{"type": "text", "data": {"text": "Hello"}}])
await self.api.send_private_msg(user_id, message=[...])
await self.api.delete_msg(message_id)
await self.api.send_forward_msg(message_type, target_id, messages=[...])
await self.api.send_poke(group_id, user_id)
```

### Sugar — 群消息

```python
await self.api.post_group_msg(group_id, text="Hello", at=user_id, image="pic.jpg", reply=msg_id)
await self.api.send_group_text(group_id, "文本")
await self.api.send_group_plain_text(group_id, "纯文本段")
await self.api.send_group_image(group_id, "https://example.com/pic.jpg")
await self.api.send_group_video(group_id, "https://example.com/video.mp4")
await self.api.send_group_record(group_id, "https://example.com/audio.mp3")
await self.api.send_group_file(group_id, "/path/to/file.pdf", name="文档.pdf")
await self.api.send_group_sticker(group_id, Image(file="sticker.gif", sub_type=1))
await self.api.post_group_array_msg(group_id, msg_array)
await self.api.post_group_forward_msg(group_id, forward)
await self.api.send_group_forward_msg_by_id(group_id, [msg_id1, msg_id2])
```

### Sugar — 私聊消息

```python
await self.api.post_private_msg(user_id, text="Hello", image="pic.jpg")
await self.api.send_private_text(user_id, "文本")
await self.api.send_private_plain_text(user_id, "纯文本段")
await self.api.send_private_image(user_id, "https://example.com/pic.jpg")
await self.api.send_private_video(user_id, "https://example.com/video.mp4")
await self.api.send_private_record(user_id, "https://example.com/audio.mp3")
await self.api.send_private_file(user_id, "/path/to/file.pdf", name="文档.pdf")
await self.api.send_private_sticker(user_id, Image(file="sticker.gif", sub_type=1))
await self.api.send_private_dice(user_id, value=1)
await self.api.send_private_rps(user_id, value=1)
await self.api.post_private_array_msg(user_id, msg_array)
await self.api.post_private_forward_msg(user_id, forward)
await self.api.send_private_forward_msg_by_id(user_id, [msg_id1, msg_id2])
```

## 群管理 API

> 参考文档：[reference/api/2_manage_api.md](docs/reference/api/2_manage_api.md)

通过 `self.api.manage.*` 访问：

```python
await self.api.manage.set_group_kick(group_id, user_id, reject_add_request=False)
await self.api.manage.set_group_ban(group_id, user_id, duration=1800)
await self.api.manage.set_group_whole_ban(group_id, enable=True)
await self.api.manage.set_group_admin(group_id, user_id, enable=True)
await self.api.manage.set_group_card(group_id, user_id, card="新名片")
await self.api.manage.set_group_name(group_id, name="新群名")
await self.api.manage.set_group_leave(group_id, is_dismiss=False)
await self.api.manage.set_group_special_title(group_id, user_id, special_title="头衔")
await self.api.manage.kick_and_block(group_id, user_id, message_id=None)
await self.api.manage.set_friend_add_request(flag, approve=True, remark="")
await self.api.manage.set_group_add_request(flag, sub_type, approve=True, reason="")
```

## 信息查询 API

> 参考文档：[reference/api/3_info_support_api.md](docs/reference/api/3_info_support_api.md)

通过 `self.api.info.*` 访问：

```python
info = await self.api.info.get_login_info()
info = await self.api.info.get_stranger_info(user_id)
friends = await self.api.info.get_friend_list()
info = await self.api.info.get_group_info(group_id)
groups = await self.api.info.get_group_list()
member = await self.api.info.get_group_member_info(group_id, user_id)
members = await self.api.info.get_group_member_list(group_id)
msg = await self.api.info.get_msg(message_id)
fwd = await self.api.info.get_forward_msg(message_id)
files = await self.api.info.get_group_root_files(group_id)
url = await self.api.info.get_group_file_url(group_id, file_id)
```

## 辅助操作 API

通过 `self.api.support.*` 访问：

```python
await self.api.support.upload_group_file(group_id, file="/path/to/file", name="name.txt")
await self.api.support.delete_group_file(group_id, file_id)
await self.api.support.send_like(user_id, times=1)
```

## 事件实体快捷方法

```python
# MessageEvent
await event.reply("文本")
await event.delete()

# GroupMessageEvent
await event.kick()
await event.ban(duration=600)

# RequestEvent
await event.approve()
await event.reject(reason="理由")
```

## API action 名称映射

测试中使用 `h.api_called("action_name")` 验证调用：

| action | 方法 |
|--------|------|
| `"send_group_msg"` | `send_group_msg()` / `post_group_msg()` / `send_group_text()` 等 |
| `"send_private_msg"` | `send_private_msg()` / `post_private_msg()` 等 |
| `"delete_msg"` | `delete_msg()` |
| `"send_forward_msg"` | `send_forward_msg()` / `post_group_forward_msg()` 等 |
| `"send_poke"` | `send_poke()` |
| `"set_group_kick"` | `manage.set_group_kick()` |
| `"set_group_ban"` | `manage.set_group_ban()` |
| `"set_group_whole_ban"` | `manage.set_group_whole_ban()` |
| `"set_group_admin"` | `manage.set_group_admin()` |
| `"set_group_card"` | `manage.set_group_card()` |
| `"set_group_name"` | `manage.set_group_name()` |
| `"set_group_leave"` | `manage.set_group_leave()` |
| `"set_friend_add_request"` | `manage.set_friend_add_request()` |
| `"set_group_add_request"` | `manage.set_group_add_request()` |
| `"get_login_info"` | `info.get_login_info()` |
| `"get_stranger_info"` | `info.get_stranger_info()` |
| `"get_friend_list"` | `info.get_friend_list()` |
| `"get_group_info"` | `info.get_group_info()` |
| `"get_group_list"` | `info.get_group_list()` |
| `"get_group_member_info"` | `info.get_group_member_info()` |
| `"get_group_member_list"` | `info.get_group_member_list()` |
| `"get_msg"` | `info.get_msg()` |
| `"get_forward_msg"` | `info.get_forward_msg()` |
| `"upload_group_file"` | `support.upload_group_file()` |
| `"get_group_root_files"` | `info.get_group_root_files()` |
| `"get_group_file_url"` | `info.get_group_file_url()` |
| `"delete_group_file"` | `support.delete_group_file()` |
| `"send_like"` | `support.send_like()` |
