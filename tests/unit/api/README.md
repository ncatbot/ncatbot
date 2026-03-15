# API 模块测试

源码模块: `ncatbot.api`

## 验证规范

### BotAPIClient (`test_api_client.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| A-01 | 高频方法平铺 | `send_group_msg` 等可直接调用 |
| A-02 | `manage` 命名空间 | 包含 `set_group_kick` 等群管操作 |
| A-03 | `info` 命名空间 | 包含 `get_group_info` 等查询操作 |
| A-04 | `__getattr__` 兜底 | 未定义方法透传到底层 API |
