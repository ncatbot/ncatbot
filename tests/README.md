# NcatBot 测试套件

基于规范驱动测试设计（Spec-Driven Test Design），覆盖 NcatBot 框架核心功能。

## 目录结构

```
tests/
├── unit/              # 单元测试 — 按模块组织
│   ├── types/         # 类型系统 (T-01 ~ T-14, S-01 ~ S-10, CQ-01 ~ CQ-08)
│   ├── event/         # 事件工厂 (E-01 ~ E-07)
│   ├── api/           # API 客户端 (A-01 ~ A-04)
│   ├── core/          # 核心分发与注册 (D-01 ~ D-09, K-01 ~ K-07, H-01 ~ H-12, R-01 ~ R-06)
│   ├── service/       # 服务管理 (S-01 ~ S-08)
│   ├── plugin/        # 插件 Mixin (M-01 ~ M-41)
│   └── adapter/       # 适配器解析 (P-01 ~ P-07, RD-01 ~ RD-03)
├── integration/       # 集成测试 (I-01 ~ I-21)
├── e2e/               # 端到端测试
│   ├── test_bot_client.py  # BotClient E2E (B-01 ~ B-05)
│   └── napcat/        # NapCat 真实连接 E2E (NC-01 ~ NC-21)
├── test_factory.py    # 工厂函数基础验证
├── test_api_calls.py  # API 调用记录验证
└── test_event_dispatch.py  # 事件分发路由验证
```

## 运行测试

```bash
# 全部测试
python -m pytest tests/ -v

# 单元测试
python -m pytest tests/unit/ -v

# 带覆盖率
python -m pytest tests/ --cov=ncatbot --cov-report=term-missing -v

# 指定模块
python -m pytest tests/unit/core/ -v

# NapCat E2E (需要真实连接，通过环境变量配置)
# $env:NAPCAT_TEST_GROUP="123456"; $env:NAPCAT_TEST_USER="654321"
python -m pytest tests/e2e/napcat/ -m napcat -v

# 数据驱动测试 (需要 dev/data.txt 或设置 NCATBOT_TEST_DATA_FILE)
python -m pytest tests/unit/adapter/test_real_data.py -v
```

## 测试基础设施

| 组件 | 说明 |
|------|------|
| `ncatbot.testing.TestHarness` | 集成/E2E 测试脚手架，管理 MockAdapter + Dispatcher + HandlerDispatcher 生命周期 |
| `ncatbot.testing.factory` | 事件数据工厂函数，生成合法的 GroupMessage / PrivateMessage / Notice / Request 数据 |
| `ncatbot.adapter.mock.MockBotAPI` | Mock API 实现，记录所有 API 调用到 `call_log` |
| `ncatbot.adapter.mock.MockAdapter` | Mock 适配器，支持手动注入事件 |

## 规范编号体系

| 前缀 | 模块 | 范围 |
|------|------|------|
| T | Types / Segments | T-01 ~ T-14 |
| S (types) | Segment 解析 (parse_segment) | S-01 ~ S-10 |
| CQ | CQ 码解析 | CQ-01 ~ CQ-08 |
| E | Event Entity / Factory | E-01 ~ E-07 |
| A | API Client | A-01 ~ A-04 |
| P | EventParser / NapCatEventParser | P-01 ~ P-07 |
| RD | 真实数据驱动解析 | RD-01 ~ RD-03 |
| D | AsyncEventDispatcher | D-01 ~ D-09 |
| K | Hook System | K-01 ~ K-07 |
| H | HandlerDispatcher | H-01 ~ H-12 |
| R | Registrar | R-01 ~ R-06 |
| S (svc) | ServiceManager | S-01 ~ S-08 |
| M | Plugin Mixin | M-01 ~ M-41 |
| I | Integration | I-01 ~ I-21 |
| B | BotClient E2E | B-01 ~ B-05 |
| NC | NapCat E2E | NC-01 ~ NC-21 |
