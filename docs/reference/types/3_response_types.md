# API 响应类型

> `ncatbot.types.napcat` 模块 — 所有 Bot API 返回值的 Pydantic 类型定义。

---

## 设计理念

NcatBot 5.0 的类型系统遵循 **上层业务只拿业务数据** 的原则：

- **Adapter 层** 负责解析 OneBot 协议信封（`status`, `retcode`, `data`, `message`），在 `retcode != 0` 时自动抛出 `APIError`
- **上层（插件/BotAPIClient）** 拿到的是纯业务类型（如 `SendMessageResult`、`GroupInfo`），无需关心 HTTP 细节

所有响应类型继承 `NapCatModel`，基于 Pydantic `BaseModel`，具有以下特性：
- `extra="allow"`：容忍协议新增字段，不会因为未知字段报错
- `_coerce_ids`：所有 `*_id` 字段自动转为 `str`
- 字典兼容：支持 `result["field"]`、`result.get("field")`、`"field" in result` 语法

```python
from ncatbot.types import SendMessageResult, LoginInfo, GroupInfo
```python

---

## 错误处理

当 API 调用返回非零 `retcode` 时，adapter 层自动抛出异常：

```python
from ncatbot.api import APIError, APIRequestError, APIPermissionError, APINotFoundError

try:
    result = await api.send_group_msg(group_id, msg)
except APINotFoundError:
    print("目标不存在")
except APIPermissionError:
    print("权限不足")
except APIError as e:
    print(f"API 错误: retcode={e.retcode}, message={e.message}")
```python

| 异常类 | retcode | 含义 |
|--------|---------|------|
| `APIError` | 任意非零 | 基类 |
| `APIRequestError` | 1400 | 请求参数错误 |
| `APIPermissionError` | 1401 | 权限不足 |
| `APINotFoundError` | 1404 | 目标不存在 |

---

## 消息类型 (`message`)

### SendMessageResult

发送消息后的返回值。

```python
result = await api.post_group_msg(group_id, text="hello")
print(result.message_id)  # str
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| message_id | str | 发送的消息 ID |

适用方法：`send_group_msg`、`send_private_msg`、`send_forward_msg`、`post_group_msg`、`post_private_msg` 及所有 sugar 发送方法。

### MessageSender

消息发送者信息（`MessageData` 内嵌）。

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | QQ 号 |
| nickname | str \| None | 昵称 |
| card | str \| None | 群名片 |
| role | str \| None | 角色（仅群消息: `owner` / `admin` / `member`） |

### MessageData

单条消息详情。

```python
msg = await api.info.get_msg(msg_id)
print(msg.sender.nickname, msg.raw_message)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| message_id | str | 消息 ID |
| real_id | int \| None | 真实消息 ID |
| time | int \| None | 发送时间戳 |
| message_type | str \| None | `"group"` / `"private"` |
| sender | MessageSender \| None | 发送者信息 |
| message | List[dict] \| None | 消息段列表（OB11 segment 格式） |
| raw_message | str \| None | 原始消息文本 |

### MessageHistory

消息历史记录。

```python
history = await api.get_group_msg_history(group_id)
for msg in history.messages:
    print(msg.sender.nickname, msg.raw_message)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| messages | List[MessageData] | 消息列表 |

### ForwardMessageData

合并转发消息内容。

| 字段 | 类型 | 说明 |
|------|------|------|
| messages | List[MessageData] | 转发消息节点列表 |

---

## 群组类型 (`group`)

### GroupInfo

```python
info = await api.info.get_group_info(group_id)
print(info.group_name, info.member_count)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| group_id | str | 群号 |
| group_name | str \| None | 群名 |
| member_count | int \| None | 当前成员数 |
| max_member_count | int \| None | 最大成员数 |

### GroupMemberInfo

```python
member = await api.info.get_group_member_info(group_id, user_id)
print(member.nickname, member.role)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| group_id | str | 群号 |
| user_id | str | 用户 QQ 号 |
| nickname | str \| None | 昵称 |
| card | str \| None | 群名片 |
| sex | str \| None | 性别 |
| age | int \| None | 年龄 |
| area | str \| None | 地区 |
| join_time | int \| None | 入群时间戳 |
| last_sent_time | int \| None | 最后发言时间戳 |
| level | str \| None | 群等级 |
| role | str \| None | 角色（`owner` / `admin` / `member`） |
| title | str \| None | 专属头衔 |
| title_expire_time | int \| None | 头衔过期时间 |
| unfriendly | bool \| None | 是否不良记录 |
| card_changeable | bool \| None | 是否可修改名片 |

### GroupHonorInfo / GroupAtAllRemain / GroupSystemMsg / GroupInfoEx

### HonorUser

群荣誉用户条目（`GroupHonorInfo` 内嵌）。

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | QQ 号 |
| nickname | str \| None | 昵称 |
| avatar | str \| None | 头像 URL |
| description | str \| None | 描述 |

### GroupHonorInfo

```python
honor = await api.info.get_group_honor_info(group_id, type="all")
if honor.current_talkative:
    print(honor.current_talkative.nickname)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| group_id | str | 群号 |
| current_talkative | HonorUser \| None | 当前龙王 |
| talkative_list | List[HonorUser] \| None | 历史龙王列表 |
| performer_list | List[HonorUser] \| None | 群聊之火列表 |
| legend_list | List[HonorUser] \| None | 群聊炽焰列表 |
| strong_newbie_list | List[HonorUser] \| None | 冒尖小春笋列表 |
| emotion_list | List[HonorUser] \| None | 快乐之源列表 |

### GroupAtAllRemain

| 字段 | 类型 | 说明 |
|------|------|------|
| can_at_all | bool | 是否可以 @全体成员 |
| remain_at_all_count_for_group | int | 群内今日剩余 @全体 次数 |
| remain_at_all_count_for_uin | int | 个人今日剩余 @全体 次数 |

### GroupNotice

```python
notices = await api.info.get_group_notice(group_id)
for n in notices:
    print(n.message.text if n.message else "")
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| notice_id | str | 公告 ID |
| sender_id | str | 发布者 QQ 号 |
| publish_time | int \| None | 发布时间戳 |
| message | GroupNoticeMessage \| None | 公告内容 |
| settings | GroupNoticeSettings \| None | 公告设置 |
| read_num | int \| None | 已读人数 |

**GroupNoticeMessage**（内嵌）：

| 字段 | 类型 | 说明 |
|------|------|------|
| text | str \| None | 文本内容 |
| image | list \| None | 图片列表 |
| images | list \| None | 图片列表（备用） |

### EssenceMessage

```python
essences = await api.info.get_essence_msg_list(group_id)
for e in essences:
    print(e.sender_nick, e.content)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| sender_id | str | 发送者 QQ 号 |
| sender_nick | str \| None | 发送者昵称 |
| operator_id | str | 设精操作者 QQ 号 |
| operator_nick | str \| None | 操作者昵称 |
| operator_time | int \| None | 操作时间戳 |
| message_id | str | 消息 ID |
| msg_seq | int \| None | 消息序列号 |
| msg_random | int \| None | 消息随机数 |
| content | List[dict] \| None | 消息内容段列表 |

### GroupShutInfo

```python
shut_list = await api.info.get_group_shut_list(group_id)
for s in shut_list:
    print(s.uin, s.nick, s.shutUpTime)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| uid | str \| None | 用户 UID（NapCat 内部标识） |
| uin | str | QQ 号 |
| nick | str \| None | 昵称 |
| shutUpTime | int \| None | 禁言结束时间戳 |
| role | int \| None | 角色 |
| cardName | str \| None | 群名片 |
| memberLevel | int \| None | 群等级 |

### GroupSystemRequest

群系统消息中的请求条目。

| 字段 | 类型 | 说明 |
|------|------|------|
| request_id | str | 请求 ID |
| invitor_uin | str | 邀请者 QQ 号 |
| invitor_nick | str \| None | 邀请者昵称 |
| group_id | str | 群号 |
| group_name | str \| None | 群名 |
| checked | bool \| None | 是否已处理 |
| actor | str | 处理者 |

### GroupSystemMsg

| 字段 | 类型 | 说明 |
|------|------|------|
| invited_requests | List[GroupSystemRequest] \| None | 邀请加群请求 |
| join_requests | List[GroupSystemRequest] \| None | 主动加群请求 |

### GroupInfoEx

群扩展信息，NapCat 扩展 API，字段由服务端决定。通过 `extra="allow"` 接收所有字段。

```python
info_ex = await api.info.get_group_info_ex(group_id)
```python

---

## 用户类型 (`user`)

### LoginInfo

```python
info = await api.info.get_login_info()
print(info.user_id, info.nickname)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | Bot QQ 号 |
| nickname | str \| None | Bot 昵称 |

### StrangerInfo

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | QQ 号 |
| nickname | str \| None | 昵称 |
| sex | str \| None | 性别 |
| age | int \| None | 年龄 |

### FriendInfo

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | QQ 号 |
| nickname | str \| None | 昵称 |
| remark | str \| None | 备注名 |

---

## 文件类型 (`file`)

### GroupFileSystemInfo

| 字段 | 类型 | 说明 |
|------|------|------|
| file_count | int | 文件数量 |
| limit_count | int | 文件上限 |
| used_space | int | 已用空间 |
| total_space | int | 总空间 |

### GroupFileInfo

群文件条目（`GroupFileList` 内嵌）。

| 字段 | 类型 | 说明 |
|------|------|------|
| group_id | str | 群号 |
| file_id | str | 文件 ID |
| file_name | str \| None | 文件名 |
| busid | int \| None | 业务 ID |
| size | int \| None | 文件大小 |
| file_size | int \| None | 文件大小（备用） |
| upload_time | int \| None | 上传时间戳 |
| dead_time | int \| None | 过期时间戳 |
| modify_time | int \| None | 修改时间戳 |
| download_times | int \| None | 下载次数 |
| uploader | str | 上传者 QQ 号 |
| uploader_name | str \| None | 上传者昵称 |

### GroupFolderInfo

群文件夹条目（`GroupFileList` 内嵌）。

| 字段 | 类型 | 说明 |
|------|------|------|
| group_id | str | 群号 |
| folder_id | str | 文件夹 ID |
| folder_name | str \| None | 文件夹名 |
| create_time | int \| None | 创建时间戳 |
| creator | str | 创建者 QQ 号 |
| creator_name | str \| None | 创建者昵称 |
| total_file_count | int \| None | 文件夹内文件数 |

### GroupFileList

```python
files = await api.info.get_group_root_files(group_id)
for f in files.files or []:
    print(f.file_name, f.file_size)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| files | List[GroupFileInfo] \| None | 文件列表 |
| folders | List[GroupFolderInfo] \| None | 文件夹列表 |

### CreateFolderResult

创建群文件夹后的返回结果。

```python
result = await api.support.create_group_file_folder(group_id, "新文件夹")
if result.groupItem and result.groupItem.folderInfo:
    print(result.groupItem.folderInfo.folderId)
```python

### FileData

通用文件数据。

| 字段 | 类型 | 说明 |
|------|------|------|
| file | str \| None | 文件路径 |
| file_name | str \| None | 文件名 |
| file_size | int \| None | 文件大小 |
| url | str \| None | 文件 URL |

### DownloadResult

| 字段 | 类型 | 说明 |
|------|------|------|
| file | str | 下载后的本地文件路径 |

---

## 系统类型 (`system`)

### VersionInfo

```python
ver = await api.info.get_version_info()
print(ver.app_name, ver.app_version)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| app_name | str \| None | 应用名称 |
| protocol_version | str \| None | 协议版本 |
| app_version | str \| None | 应用版本 |

### BotStatus

| 字段 | 类型 | 说明 |
|------|------|------|
| online | bool \| None | 是否在线 |
| good | bool \| None | 状态是否正常 |

### EmojiLikeInfo

```python
emoji = await api.info.fetch_emoji_like(message_id, emoji_id="128077")
for user in emoji.emojiLikesList or []:
    print(user.nickName)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| emojiLikesList | List[EmojiLikeUser] \| None | 回应用户列表 |
| cookie | str \| None | 分页 Cookie |
| isLastPage | bool \| None | 是否最后一页 |
| isFirstPage | bool \| None | 是否第一页 |
| result | int \| None | 结果码 |
| errMsg | str \| None | 错误信息 |

**EmojiLikeUser**（内嵌）：

| 字段 | 类型 | 说明 |
|------|------|------|
| tinyId | str \| None | 用户 TinyID |
| nickName | str \| None | 昵称 |
| headUrl | str \| None | 头像 URL |

### EmojiLikesResult

```python
likes = await api.info.get_emoji_likes(message_id, emoji_id="128077")
for user in likes.emoji_like_list or []:
    print(user.user_id, user.nick_name)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| emoji_like_list | List[EmojiLikesUser] \| None | 点赞用户列表 |

**EmojiLikesUser**（内嵌）：

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | str | QQ 号 |
| nick_name | str \| None | 昵称 |

### OcrResult

```python
result = await api.info.ocr_image(image_url)
for t in result.texts or []:
    print(t.text, t.confidence)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| texts | List[OcrText] \| None | 识别文本列表 |

**OcrText**（内嵌）：

| 字段 | 类型 | 说明 |
|------|------|------|
| text | str \| None | 文本内容 |
| confidence | float \| None | 置信度 |
| coordinates | list \| None | 坐标 |

### RecentContact

```python
contacts = await api.info.get_recent_contact(count=10)
for c in contacts:
    print(c.peerName, c.msgTime)
```python

| 字段 | 类型 | 说明 |
|------|------|------|
| peerUin | str \| None | 对方 QQ 号/群号 |
| remark | str \| None | 备注 |
| msgTime | str \| None | 最后消息时间 |
| chatType | int \| None | 聊天类型（1=私聊, 2=群聊） |
| msgId | str \| None | 最后消息 ID |
| sendNickName | str \| None | 发送者昵称 |
| sendMemberName | str \| None | 发送者群名片 |
| peerName | str \| None | 对方名称 |
| lastestMsg | RecentContactMessage \| None | 最新消息详情 |

---

## 基类

### NapCatModel

所有响应类型的基类，继承自 `pydantic.BaseModel`。

```python
from ncatbot.types.napcat import NapCatModel
```python

特性：
- `ConfigDict(extra="allow", populate_by_name=True)` — 允许额外字段
- 自动将 `*_id` 字段从 `int` 转为 `str`
- 字典兼容访问：`model["key"]`、`model.get("key", default)`、`"key" in model`

---

## 源码位置

```python
ncatbot/types/napcat/
├── __init__.py     # 统一导出
├── _base.py        # NapCatModel 基类
├── message.py      # SendMessageResult, MessageSender, MessageData, MessageHistory, ForwardMessageData
├── group.py        # GroupInfo, GroupMemberInfo, GroupNotice, EssenceMessage, HonorUser, GroupHonorInfo, ...
├── user.py         # LoginInfo, StrangerInfo, FriendInfo
├── file.py         # GroupFileSystemInfo, GroupFileInfo, GroupFolderInfo, GroupFileList, CreateFolderResult, FileData, DownloadResult
└── system.py       # VersionInfo, BotStatus, EmojiLikeInfo, EmojiLikesResult, OcrResult, RecentContact
```text
