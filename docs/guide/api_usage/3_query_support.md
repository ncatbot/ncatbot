# 查询与支持操作

> `.info` 和 `.support` 命名空间的常用方法和使用场景。完整参数表见 [reference/api/3_info_support_api.md](../../reference/api/3_info_support_api.md)。

---

## 信息查询（.info 命名空间）

### 常用查询示例

```python
# 获取登录信息
info = await self.api.info.get_login_info()
# {"user_id": 10001, "nickname": "MyBot"}

# 群列表
groups = await self.api.info.get_group_list()

# 群成员信息
member = await self.api.info.get_group_member_info(event.group_id, target.qq)
# 含 nickname, card, role("owner"/"admin"/"member"), join_time

# 查询消息详情（通过消息 ID）
msg_data = await self.api.info.get_msg(message_id)
```python

### 方法速查

| 方法 | 说明 |
|------|------|
| `get_login_info()` | 获取 Bot 登录信息 |
| `get_friend_list()` | 好友列表 |
| `get_group_list()` | 群列表 |
| `get_group_member_info(gid, uid)` | 群成员详情 |
| `get_group_member_list(gid)` | 群成员列表 |
| `get_msg(message_id)` | 查询消息详情 |
| `get_stranger_info(uid)` | 陌生人信息 |
| `get_group_info(gid)` | 群信息 |
| `get_forward_msg(msg_id)` | 合并转发内容 |

---

## 文件操作（.support 命名空间）

```python
# 上传群文件
await self.api.support.upload_group_file(group_id, "/path/to/report.pdf", "月报.pdf")

# 获取群文件下载链接
url = await self.api.info.get_group_file_url(group_id, file_id)

# 删除群文件
await self.api.support.delete_group_file(group_id, file_id)
```python

> `upload_group_file` 通过群文件系统上传。以消息形式发送文件请用 `self.api.send_group_file()`。

---

## 延伸阅读

- [查询与支持 API 参考](../../reference/api/3_info_support_api.md) — 完整签名与返回值
- [消息发送指南](1_messaging.md) — 消息发送方式
    folder_id: str = "",
) -> None
```python

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `group_id` | `str \| int` | — | 群号 |
| `file` | `str` | — | 本地文件路径或 URL |
| `name` | `str` | — | 文件显示名称 |
| `folder_id` | `str` | `""` | 上传到的文件夹 ID，空为根目录 |

```python
await self.api.support.upload_group_file(
    group_id=123456,
    file="/path/to/report.pdf",
    name="月报.pdf",
)
```python

> **注意**：`upload_group_file` 通过群文件系统上传。若需要以消息形式发送文件，请使用 `self.api.send_group_file(group_id, file, name)`（sugar 方法）。

---

### delete_group_file — 删除群文件

```python
async def delete_group_file(
    self,
    group_id: Union[str, int],
    file_id: str,
) -> None
```python

| 参数 | 类型 | 说明 |
|------|------|------|
| `group_id` | `str \| int` | 群号 |
| `file_id` | `str` | 文件 ID（通过 `info.get_group_root_files` 获取） |

```python
# 获取群文件列表 → 找到目标文件 → 删除
files = await self.api.info.get_group_root_files(group_id)
for f in files.get("files", []):
    if f.get("file_name") == "旧文件.pdf":
        await self.api.support.delete_group_file(group_id, f["file_id"])
        break
```python

---

### send_like — 点赞

```python
async def send_like(
    self,
    user_id: Union[str, int],
    times: int = 1,
) -> None
```python

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `user_id` | `str \| int` | — | 目标用户 QQ |
| `times` | `int` | `1` | 点赞次数 |

```python
await self.api.support.send_like(user_id, times=10)
```python

---

## 请求处理

好友请求和加群请求通过 `manage` 命名空间进行处理。通常在 `RequestEvent` 的处理器中调用。

### set_friend_add_request — 处理好友请求

```python
async def set_friend_add_request(
    self,
    flag: str,
    approve: bool = True,
    remark: str = "",
) -> None
```python

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `flag` | `str` | — | 请求标识（从 `RequestEvent` 中获取） |
| `approve` | `bool` | `True` | `True` 同意，`False` 拒绝 |
| `remark` | `str` | `""` | 同意后的备注名 |

```python
from ncatbot.event import FriendRequestEvent

@registrar.on_friend_request()
async def on_friend_request(self, event: FriendRequestEvent):
    # 自动同意好友请求
    await self.api.manage.set_friend_add_request(
        flag=event.flag,
        approve=True,
        remark="新朋友",
    )
```python

---

### set_group_add_request — 处理群请求

```python
async def set_group_add_request(
    self,
    flag: str,
    sub_type: str,
    approve: bool = True,
    reason: str = "",
) -> None
```python

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `flag` | `str` | — | 请求标识 |
| `sub_type` | `str` | — | 请求子类型：`"add"`（加群）或 `"invite"`（邀请） |
| `approve` | `bool` | `True` | `True` 同意，`False` 拒绝 |
| `reason` | `str` | `""` | 拒绝理由（仅拒绝时有效） |

```python
from ncatbot.event import GroupRequestEvent

@registrar.on_group_request()
async def on_group_request(self, event: GroupRequestEvent):
    if event.sub_type == "invite":
        # 自动同意邀请入群
        await self.api.manage.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=True,
        )
    else:
        # 加群请求需要人工审核，先拒绝
        await self.api.manage.set_group_add_request(
            flag=event.flag,
            sub_type=event.sub_type,
            approve=False,
            reason="请联系管理员",
        )
```python

---

## 错误处理与日志

### _LoggingAPIProxy 自动日志

`BotAPIClient` 内部通过 `_LoggingAPIProxy` 代理所有底层 `IBotAPI` 的异步方法调用，自动输出 `INFO` 级别日志，格式如下：

```text
INFO  BotAPIClient API调用 send_group_msg 123456 [{"type":"text","data":{"text":"hello"}}]
```python

日志特点：
- **自动截断**：参数超过 2000 字符时自动截断并添加 `...`
- **零侵入**：无需手动记录日志，所有 API 调用都被自动追踪
- **dict/list 自动序列化**：JSON 格式，便于排查

### 异常处理最佳实践

```python
@registrar.on_group_command("踢人")
async def on_kick(self, event: GroupMessageEvent, target: At = None):
    if target is None:
        await event.reply("请 @一个用户")
        return

    try:
        await self.api.manage.set_group_kick(event.group_id, target.qq)
        await event.reply(f"已踢出 {target.qq}")
    except Exception as e:
        LOG.error(f"踢人失败: {e}")
        await event.reply("操作失败，请检查 Bot 权限")
```markdown

**建议**：

1. **权限检查在先**：调用群管理 API 前，先通过 RBAC 或 `get_group_member_info` 确认 Bot 和操作者的权限
2. **善用日志**：`_LoggingAPIProxy` 已自动记录所有调用，出错时查看 `logs/bot.log.*` 即可定位
3. **避免死循环**：在处理请求事件时，注意不要无条件触发新的请求

---

> **返回**：[Bot API 使用指南](README.md) · **相关**：[群管理详解](2_manage.md)
