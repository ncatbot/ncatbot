# Bot API 完整参考

> 参考文档：[guide/api_usage/](docs/guide/api_usage/), [reference/api/](docs/reference/api/), [reference/types/3_response_types.md](docs/reference/types/3_response_types.md)

## 响应类型与错误处理

所有 API 返回值使用 Pydantic 类型（定义在 `ncatbot.types.napcat`）：

```python
from ncatbot.types import SendMessageResult, LoginInfo, GroupInfo, GroupMemberInfo, MessageSender

# 发送消息返回 SendMessageResult
result = await self.api.post_group_msg(group_id, text="hello")
print(result.message_id)  # str

# 查询返回对应类型
info = await self.api.info.get_login_info()  # -> LoginInfo
groups = await self.api.info.get_group_list()  # -> List[GroupInfo]
member = await self.api.info.get_group_member_info(gid, uid)  # -> GroupMemberInfo
```python

错误处理：adapter 层自动解析信封，retcode 非零时抛 `APIError`：

```python
from ncatbot.api import APIError, APINotFoundError, APIPermissionError

try:
    await self.api.send_group_msg(group_id, msg)
except APINotFoundError:
    ...  # 目标不存在
except APIPermissionError:
    ...  # 权限不足
except APIError as e:
    print(e.retcode, e.message)
```python

## 消息发送 API

### 原子方法（顶层）

```python
await self.api.send_group_msg(group_id, message=[{"type": "text", "data": {"text": "Hello"}}])
await self.api.send_private_msg(user_id, message=[...])
await self.api.delete_msg(message_id)
await self.api.send_forward_msg(message_type, target_id, messages=[...])
await self.api.send_poke(group_id, user_id)

# 高频消息扩展 API（平铺到顶层）
history = await self.api.get_group_msg_history(group_id, message_seq=None, count=20)
history = await self.api.get_friend_msg_history(user_id, message_seq=None, count=20)
await self.api.set_msg_emoji_like(message_id, emoji_id, set=True)
await self.api.mark_group_msg_as_read(group_id)
await self.api.mark_private_msg_as_read(user_id)
await self.api.mark_all_as_read()
await self.api.forward_friend_single_msg(user_id, message_id)
await self.api.forward_group_single_msg(group_id, message_id)
await self.api.friend_poke(user_id)
```python

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
```python

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
```python

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

# 群公告 / 精华 / 扩展管理
await self.api.manage.send_group_notice(group_id, content, image="")
await self.api.manage.delete_group_notice(group_id, notice_id)
await self.api.manage.set_essence_msg(message_id)
await self.api.manage.delete_essence_msg(message_id)
await self.api.manage.set_group_kick_members(group_id, user_ids, reject_add_request=False)
await self.api.manage.set_group_remark(group_id, remark)
await self.api.manage.set_group_sign(group_id)
await self.api.manage.set_group_todo(group_id, message_id)
await self.api.manage.set_group_portrait(group_id, file)

# 好友管理
await self.api.manage.set_friend_remark(user_id, remark)
await self.api.manage.delete_friend(user_id)

# 个人资料
await self.api.manage.set_self_longnick(long_nick)
await self.api.manage.set_qq_avatar(file)
await self.api.manage.set_qq_profile(nickname, company, email, college, personal_note)
await self.api.manage.set_online_status(status, ext_status=0, custom_status="")
```python

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

# 群扩展查询
notices = await self.api.info.get_group_notice(group_id)
essences = await self.api.info.get_essence_msg_list(group_id)
honor = await self.api.info.get_group_honor_info(group_id, type="all")
remain = await self.api.info.get_group_at_all_remain(group_id)
shut_list = await self.api.info.get_group_shut_list(group_id)
sys_msg = await self.api.info.get_group_system_msg()
info_ex = await self.api.info.get_group_info_ex(group_id)

# 文件扩展查询
fs_info = await self.api.info.get_group_file_system_info(group_id)
files = await self.api.info.get_group_files_by_folder(group_id, folder_id)
url = await self.api.info.get_private_file_url(user_id, file_id)
file = await self.api.info.get_file(file_id)

# 消息扩展查询
emoji = await self.api.info.fetch_emoji_like(message_id, emoji_id, emoji_type="1", count=20, cookie="")  # -> EmojiLikeInfo
likes = await self.api.info.get_emoji_likes(message_id, emoji_id="", count=0)  # -> EmojiLikesResult

# 系统信息
version = await self.api.info.get_version_info()
status = await self.api.info.get_status()
recent = await self.api.info.get_recent_contact(count=10)

# OCR
result = await self.api.info.ocr_image(image)
```python

## 辅助操作 API

通过 `self.api.support.*` 访问：

```python
await self.api.support.upload_group_file(group_id, file="/path/to/file", name="name.txt")
await self.api.support.delete_group_file(group_id, file_id)
await self.api.support.send_like(user_id, times=1)

# 文件系统扩展
result = await self.api.support.create_group_file_folder(group_id, name, parent_id="")  # -> CreateFolderResult
await self.api.support.delete_group_folder(group_id, folder_id)
await self.api.support.upload_private_file(user_id, file, name)
result = await self.api.support.download_file(url="", file="", headers="")
```python

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
```python

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
| `"send_group_notice"` | `manage.send_group_notice()` |
| `"delete_group_notice"` | `manage.delete_group_notice()` |
| `"set_essence_msg"` | `manage.set_essence_msg()` |
| `"delete_essence_msg"` | `manage.delete_essence_msg()` |
| `"set_group_kick_members"` | `manage.set_group_kick_members()` |
| `"set_group_remark"` | `manage.set_group_remark()` |
| `"set_group_sign"` | `manage.set_group_sign()` |
| `"set_group_todo"` | `manage.set_group_todo()` |
| `"set_group_portrait"` | `manage.set_group_portrait()` |
| `"set_friend_remark"` | `manage.set_friend_remark()` |
| `"delete_friend"` | `manage.delete_friend()` |
| `"set_self_longnick"` | `manage.set_self_longnick()` |
| `"set_qq_avatar"` | `manage.set_qq_avatar()` |
| `"set_qq_profile"` | `manage.set_qq_profile()` |
| `"set_online_status"` | `manage.set_online_status()` |
| `"get_group_notice"` | `info.get_group_notice()` |
| `"get_essence_msg_list"` | `info.get_essence_msg_list()` |
| `"get_group_honor_info"` | `info.get_group_honor_info()` |
| `"get_group_at_all_remain"` | `info.get_group_at_all_remain()` |
| `"get_group_shut_list"` | `info.get_group_shut_list()` |
| `"get_group_system_msg"` | `info.get_group_system_msg()` |
| `"get_group_info_ex"` | `info.get_group_info_ex()` |
| `"get_group_file_system_info"` | `info.get_group_file_system_info()` |
| `"get_group_files_by_folder"` | `info.get_group_files_by_folder()` |
| `"get_private_file_url"` | `info.get_private_file_url()` |
| `"get_file"` | `info.get_file()` |
| `"fetch_emoji_like"` | `info.fetch_emoji_like()` |
| `"get_emoji_likes"` | `info.get_emoji_likes()` |
| `"get_version_info"` | `info.get_version_info()` |
| `"get_status"` | `info.get_status()` |
| `"get_recent_contact"` | `info.get_recent_contact()` |
| `"ocr_image"` | `info.ocr_image()` |
| `"create_group_file_folder"` | `support.create_group_file_folder()` |
| `"delete_group_folder"` | `support.delete_group_folder()` |
| `"upload_private_file"` | `support.upload_private_file()` |
| `"download_file"` | `support.download_file()` |
| `"get_group_msg_history"` | `get_group_msg_history()` (顶层) |
| `"get_friend_msg_history"` | `get_friend_msg_history()` (顶层) |
| `"set_msg_emoji_like"` | `set_msg_emoji_like()` (顶层) |
| `"mark_group_msg_as_read"` | `mark_group_msg_as_read()` (顶层) |
| `"mark_private_msg_as_read"` | `mark_private_msg_as_read()` (顶层) |
| `"mark_all_as_read"` | `mark_all_as_read()` (顶层) |
| `"forward_friend_single_msg"` | `forward_friend_single_msg()` (顶层) |
| `"forward_group_single_msg"` | `forward_group_single_msg()` (顶层) |
| `"friend_poke"` | `friend_poke()` (顶层) |
