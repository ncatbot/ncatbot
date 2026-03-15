# 集成测试

跨模块协作的集成测试，验证多个组件协同工作。

## 验证规范

### 事件管线 (`test_event_pipeline.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-01 | 全链路事件管线 | Dispatcher → HandlerDispatcher → handler 完整流转 |
| I-02 | 混合事件过滤 | 多类型事件混发，handler 只收到匹配的事件 |
| I-03 | Hook 过滤 + 执行 | Hook 过滤与 handler 执行全链路 |

### 插件生命周期 (`test_plugin_lifecycle.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-10 | Registrar → flush → HandlerDispatcher | `on()` 收集 → `flush_pending` → 注册到 dispatcher |
| I-11 | `revoke_plugin` 阻断 | 撤销后 handler 不再触发 |
| I-12 | 多插件隔离 | 多插件 handler 互不干扰 |
| I-13 | ContextVar 隔离 | 不同插件的 pending handler 分开管理 |

### 服务集成 (`test_service_integration.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| I-20 | 多服务加载顺序 | ServiceManager 按依赖拓扑排序加载 |
| I-21 | 服务关闭顺序 | `close_all()` 正确关闭所有服务 |
