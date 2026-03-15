# Service 模块测试

源码模块: `ncatbot.service`

## 验证规范

### ServiceManager (`test_service_manager.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| S-01 | `register()` | 注册服务类到管理器 |
| S-02 | `load()` | 加载并返回服务实例 |
| S-03 | `load_all()` | 按拓扑排序加载所有已注册服务 |
| S-04 | 循环依赖检测 | 循环依赖抛出 `ValueError` |
| S-05 | `close_all()` | 关闭所有已加载服务 |
| S-06 | `get()` | 返回已加载的服务实例 |
| S-07 | `has()` | 判断服务是否已加载 |
| S-08 | `register_builtin()` | 注册内置服务 |
