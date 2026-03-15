# Adapter 模块测试

源码模块: `ncatbot.adapter.napcat`

## 验证规范

### EventParser (`test_event_parser.py`)

测试 `EventParser` 注册表、路由推导、OB11 JSON 解析及 `NapCatEventParser` 包装器。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| P-01 | 注册表完整性 | `_registry` 包含全部 17 种内置事件类型 |
| P-02 | `_get_key()` 推导 | message/notice/request/meta_event 各 post_type 正确路由 |
| P-03 | `parse()` 解析真实 OB11 JSON | 私聊/群聊/心跳/生命周期/戳一戳/好友请求/群撤回/禁言/群增 |
| P-04 | 错误处理 | 缺失/未知 post_type → `ValueError` |
| P-05 | NapCatEventParser 包装器 | 缺 post_type → `None`，未知类型 → `None` |
| P-06 | message_sent 映射 | `message_sent` 映射到 `MESSAGE` + `message_type` |
| P-07 | notify 子类型推导 | `notice_type=notify` 时使用 `sub_type` 推导 |

### 真实数据驱动解析 (`test_real_data.py`)

使用真实 OB11 数据文件验证解析器的兼容性（无数据文件时自动 skip）。

**数据来源优先级:**
1. 环境变量 `NCATBOT_TEST_DATA_FILE` 指定的文件路径
2. 默认路径 `dev/data.txt`

**文件格式:** 每行一条 JSON/Python-dict，包含 `post_type` 字段即为有效事件。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| RD-01 | 全量事件解析 | 数据文件中每条事件都能被 `EventParser.parse()` 成功解析 |
| RD-02 | 消息段逐个解析 | 消息事件中的每个 segment 都能被 `parse_segment()` 解析 |
| RD-03 | post_type 一致性 | 解析后 `post_type` 与原始数据一致 |

## 运行方式

```bash
# 运行 EventParser 单元测试（无外部依赖）
python -m pytest tests/unit/adapter/test_event_parser.py -v

# 运行数据驱动测试（需要数据文件）
python -m pytest tests/unit/adapter/test_real_data.py -v

# 指定自定义数据文件
$env:NCATBOT_TEST_DATA_FILE="path/to/data.txt"
python -m pytest tests/unit/adapter/test_real_data.py -v
```
