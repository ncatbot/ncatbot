# 测试规范编号

框架测试使用规范编号标识每个测试用例，格式为 `前缀-序号`。

## 编号表

| 前缀 | 模块 | 范围 | 测试文件位置 |
|------|------|------|-------------|
| T | Types / Segments | T-01 ~ T-14 | `tests/unit/types/` |
| S (types) | Segment 解析 (parse_segment) | S-01 ~ S-10 | `tests/unit/types/` |
| CQ | CQ 码解析 | CQ-01 ~ CQ-08 | `tests/unit/types/` |
| E | Event Entity / Factory | E-01 ~ E-07 | `tests/unit/event/` |
| A | API Client | A-01 ~ A-04 | `tests/unit/api/` |
| P | EventParser / NapCatEventParser | P-01 ~ P-07 | `tests/unit/adapter/` |
| RD | 真实数据驱动解析 | RD-01 ~ RD-03 | `tests/unit/adapter/` |
| D | AsyncEventDispatcher | D-01 ~ D-09 | `tests/unit/core/` |
| K | Hook System | K-01 ~ K-07 | `tests/unit/core/` |
| H | HandlerDispatcher | H-01 ~ H-12 | `tests/unit/core/` |
| R | Registrar | R-01 ~ R-06 | `tests/unit/core/` |
| S (svc) | ServiceManager | S-01 ~ S-08 | `tests/unit/service/` |
| M | Plugin Mixin | M-01 ~ M-41 | `tests/unit/plugin/` |
| I | Integration | I-01 ~ I-21 | `tests/integration/` |
| B | BotClient E2E | B-01 ~ B-05 | `tests/e2e/` |
| NC | NapCat E2E | NC-01 ~ NC-21 | `tests/e2e/napcat/` |

## 命名规范

测试函数的 docstring 第一行包含规范编号：

```python
async def test_dispatcher_routes_group_message(event_dispatcher):
    """D-03: AsyncEventDispatcher 正确路由群消息到 message.group 订阅者"""
    ...
```python

## 新增测试编号

在对应前缀的最大序号上 +1。例如现有 D-01 ~ D-09，新增时使用 D-10。
