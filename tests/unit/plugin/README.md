# Plugin Mixin 模块测试

源码模块: `ncatbot.plugin.mixin`

## 验证规范

### ConfigMixin (`test_config_mixin.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| M-01 | `_mixin_load()` | 从 YAML 文件加载配置 |
| M-02 | `set_config()` | 设置配置项后立即持久化 |
| M-03 | `get_config(key, default)` | key 不存在时返回默认值 |
| M-04 | `remove_config()` | 移除配置项，返回 `bool` |
| M-05 | `update_config()` | 批量更新多个配置项 |
| M-06 | 配置文件不存在 | 优雅返回空字典 |

### DataMixin (`test_data_mixin.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| M-10 | `_mixin_load()` | 从 JSON 文件加载数据 |
| M-11 | `_mixin_unload()` | 将数据保存到 JSON |
| M-12 | 数据文件不存在 | 优雅返回空字典 |

### EventMixin (`test_event_mixin.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| M-20 | `events()` | 返回 EventStream 并追踪到 `_active_streams` |
| M-21 | `wait_event(timeout)` | 超时抛出 `TimeoutError` |
| M-22 | `_mixin_unload()` | 关闭所有活跃 stream |

### TimeTaskMixin (`test_time_task_mixin.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| M-30 | `add_scheduled_task` | 服务可用时返回 `True` |
| M-31 | `remove_scheduled_task` | 服务可用时返回 `True` |
| M-32 | 服务不可用 | 优雅返回 `False` / `None` |
| M-33 | `get_task_status` | 服务可用时返回状态信息 |

### RBACMixin (`test_rbac_mixin.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| M-40 | 权限/角色操作 | `check_permission` / `add_permission` / `add_role` 等代理到 RBACService |
| M-41 | 服务不可用 | 所有操作返回 `False` |
