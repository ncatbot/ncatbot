# 端到端测试

## BotClient E2E (`test_bot_client.py`)

使用 `TestHarness` 进行完整 BotClient 模拟测试。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| B-01 | TestHarness 生命周期 | `start()` / `stop()` 以及 async context manager |
| B-02 | 事件→handler→API | 注入事件后 handler 执行并产生 API 调用记录 |
| B-03 | 多事件流水线 | 连续注入多个事件，handler 依次处理 |
| B-04 | `reply()` API | handler 调用 `event.reply()` 产生正确的 API 调用 |
| B-05 | `settle()` 等待 | `settle()` 阻塞直到所有 handler 处理完成 |

### 测试基础设施

- **TestHarness**: 一站式集成测试脚手架，封装 MockAdapter + Dispatcher + HandlerDispatcher
- **`inject(data)`**: 注入事件数据触发处理流程
- **`settle()`**: 等待所有排队事件处理完毕
- **`reset_api()`**: 清空 API 调用日志

## NapCat E2E (`napcat/`)

需要真实 NapCat WebSocket 连接的端到端测试。
不使用 pytest，直接通过 `BotClient` 框架管理会话，引导式顺序执行。

### 配置

连接参数从 `config.yaml` 读取（`napcat.ws_uri` / `napcat.ws_token`）。
测试目标通过环境变量指定：

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NAPCAT_TEST_GROUP` | 测试群号 (必填) | — |
| `NAPCAT_TEST_USER` | 测试用户 QQ (必填) | — |

### 验证规范

| 规范 ID | 场景 | 说明 |
|---------|------|------|
| NC-01 | 基础信息 | `get_login_info` |
| NC-02 | 基础信息 | `get_friend_list` |
| NC-03 | 基础信息 | `get_group_list` |
| NC-04 | 基础信息 | `get_group_info` |
| NC-05 | 基础信息 | `get_group_member_list` |
| NC-06 | 基础信息 | `get_stranger_info` |
| NC-10 | 群消息 | 发送群文本消息 |
| NC-11 | 群消息 | 查询消息详情 |
| NC-12 | 群消息 | 撤回消息 |
| NC-13 | 群消息 | 发送简单文本 |
| NC-20 | 好友互动 | 发送私聊消息 |

### 运行方式

```powershell
# 配置环境变量
$env:NAPCAT_TEST_GROUP = "123456"
$env:NAPCAT_TEST_USER = "654321"

# 运行 NapCat E2E 测试 (需要 NapCat 服务已启动)
python tests/e2e/napcat/run.py
```
