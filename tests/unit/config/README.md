# Config 模块测试

源码模块: `ncatbot.utils.config`

## 验证规范

### Config Migration (`test_config_migration.py`)

测试旧版 `napcat` 配置格式到新版 `adapters` 格式的自动迁移，以及 `Config` 模型的字段校验。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CF-01 | 旧格式自动迁移 | 旧 `napcat` dict → `adapters` 列表 + `_migrated=True` |
| CF-02 | 新格式不迁移 | 已有 `adapters` → 不触发迁移、`_migrated=False` |
| CF-03 | 两者都无 | 无 `napcat` 也无 `adapters` → 默认 napcat adapter |
| CF-04 | AdapterEntry 字段验证 | 字段类型、必填项校验 |
| CF-05 | 字段 coerce / clamp | `bot_uin`/`root` 整数强转、`websocket_timeout` 范围限制 |
