# 测试 API 速查

## TestHarness

| 属性/方法 | 签名 | 说明 |
|-----------|------|------|
| `bot` | `BotClient` | BotClient 实例 |
| `adapter` | `MockAdapter` | MockAdapter 实例 |
| `mock_api` | `MockBotAPI` | API mock，用于断言 |
| `dispatcher` | `AsyncEventDispatcher` | 事件分发器 |
| `start()` | `async` | 启动 BotClient |
| `stop()` | `async` | 停止 BotClient |
| `inject(event_data)` | `async` | 注入单个事件 |
| `inject_many(events)` | `async` | 注入多个事件 |
| `settle(delay=0.05)` | `async` | 等待 handler 执行完 |
| `wait_event(predicate, timeout=2.0)` | `async` | 等待满足条件的事件 |
| `api_calls` | `list[APICall]` | 所有 API 调用记录 |
| `api_called(action)` | `bool` | 是否调用过某 action |
| `api_call_count(action)` | `int` | 某 action 的调用次数 |
| `get_api_calls(action)` | `list[APICall]` | 某 action 的所有调用 |
| `last_api_call(action)` | `APICall` | 某 action 最近一次调用 |
| `reset_api()` | `void` | 清空调用记录 |

## PluginTestHarness（继承 TestHarness）

| 参数/方法 | 签名 | 说明 |
|-----------|------|------|
| `plugin_names` | `list[str]` | 构造参数：要加载的插件名 |
| `plugin_dir` | `Path` | 构造参数：插件目录 |
| `skip_builtin` | `bool = True` | 构造参数：是否跳过内置插件 |
| `loaded_plugins` | `list[str]` | 已加载插件名列表 |
| `get_plugin(name)` | `NcatBotPlugin` | 获取插件实例 |
| `plugin_config(name)` | `dict` | 获取插件配置 |
| `plugin_data(name)` | `dict` | 获取插件数据 |
| `reload_plugin(name)` | `async` | 热重载插件 |

## 事件工厂函数

| 函数 | 返回类型 | 关键参数（均有默认值） |
|------|---------|----------------------|
| `group_message(text)` | `GroupMessageEventData` | `group_id`, `user_id`, `self_id` |
| `private_message(text)` | `PrivateMessageEventData` | `user_id`, `self_id` |
| `friend_request()` | `FriendRequestEventData` | `user_id`, `comment` |
| `group_request()` | `GroupRequestEventData` | `user_id`, `group_id`, `comment` |
| `group_increase()` | `GroupIncreaseNoticeEventData` | `user_id`, `group_id`, `operator_id` |
| `group_decrease()` | `GroupDecreaseNoticeEventData` | `user_id`, `group_id`, `operator_id` |
| `group_ban()` | `GroupBanNoticeEventData` | `user_id`, `group_id`, `duration` |
| `poke()` | `PokeNotifyEventData` | `user_id`, `target_id`, `group_id` |

默认值：`user_id="99999"`, `group_id="100200"`, `self_id="10001"`

## MockBotAPI

| 方法 | 说明 |
|------|------|
| `set_response(action, response)` | 预设某 action 的返回值 |
| `calls` | 所有 `APICall` 记录 |
| `called(action)` | `bool` |
| `call_count(action)` | `int` |
| `get_calls(action)` | `list[APICall]` |
| `last_call(action)` | `APICall` |
| `reset()` | 清空记录 |

## APICall 数据类

```python
@dataclass
class APICall:
    action: str       # API action 名称
    args: tuple       # 位置参数
    kwargs: dict      # 关键字参数
    timestamp: float  # 调用时间
```python

## Scenario 链式构建器

```python
Scenario(harness)
    .inject(event_data)          # 注入事件
    .settle(delay=0.05)          # 等待处理
    .assert_api_called(action)   # 断言调用
    .run()                       # 执行链（async）
```python

## pytest Fixtures（conftest.py 提供）

| Fixture | 作用域 | 说明 |
|---------|--------|------|
| `mock_adapter` | function | 独立 MockAdapter |
| `harness` | function | TestHarness（async with 管理） |
| `mock_api` | function | MockBotAPI |
| `event_dispatcher` | function | AsyncEventDispatcher |
| `handler_dispatcher` | function | HandlerDispatcher（注入 mock_api） |
| `fresh_registrar` | function | 清理全局 pending 后的 Registrar |
| `tmp_plugin_workspace` | function | 临时插件工作目录（tmp_path） |
