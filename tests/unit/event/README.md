# Event 模块测试

源码模块: `ncatbot.event`

## 验证规范

### 事件实体工厂 (`test_event_factory.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| E-01 | GroupMessageEventData 映射 | `create_entity()` 返回 `GroupMessageEvent` |
| E-02 | PrivateMessageEventData 映射 | `create_entity()` 返回 `PrivateMessageEvent` |
| E-03 | 未知 post_type 降级 | 未知类型降级到 `BaseEvent` |
| E-04 | `__getattr__` 属性代理 | EventEntity 代理底层 EventData 字段 |
| E-05 | `MessageEvent.reply()` | 调用对应 API 发送消息 |
| E-06 | `GroupMessageEvent.kick()/ban()` | 调用正确的群管 API |
| E-07 | `RequestEvent.approve()/reject()` | 调用正确的请求处理 API |

### 关键实现细节

- `MockBotAPI._record()` 将所有参数存储在 `APICall.args` 元组中（即使使用关键字参数调用）
- 测试中通过 `call.args[N]` 而非 `call.kwargs` 来验证参数
