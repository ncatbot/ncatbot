# Message Event Types 测试方案

本目录包含对 `ncatbot.core.event.message_event.types` 模块的完整测试套件。

## 测试结构

```
test/core/event/
├── conftest.py          # pytest 配置和测试数据加载器
├── data.txt             # 真实的测试数据（从日志提取）
├── test_base.py         # base.py 模块测试
├── test_primitives.py   # primitives.py 模块测试  
├── test_media.py        # media.py 模块测试
├── test_misc.py         # misc.py 模块测试
├── test_forward.py      # forward.py 模块测试
├── test_integration.py  # 集成测试
└── README.md            # 本文件
```

## 测试数据管理

### 数据格式

测试数据存储在 `.txt` 文件中，支持两种格式：

1. **日志格式** - 从应用日志中提取的事件数据：
   ```
   [时间戳] DEBUG Adapter ... | 收到事件: {'type': 'message', ...}
   ```

2. **纯 JSON/Python 格式** - 直接的事件数据（支持单引号和双引号）

### 添加新测试数据

只需将新的测试数据添加到 `data.txt` 文件中，测试框架会自动加载并解析。

## 测试数据提供器

`conftest.py` 中的 `TestDataProvider` 类提供以下功能：

- **按类型获取消息段**: `get_segments_by_type("text")`, `get_segments_by_type("image")` 等
- **获取所有消息事件**: `message_events` 属性
- **获取所有元事件**: `meta_events` 属性
- **查看可用类型**: `available_segment_types` 属性

### 可用的 Fixtures

| Fixture | 描述 |
|---------|------|
| `data_provider` | TestDataProvider 实例 |
| `text_segments` | 所有文本消息段 |
| `image_segments` | 所有图片消息段 |
| `face_segments` | 所有表情消息段 |
| `at_segments` | 所有@消息段 |
| `reply_segments` | 所有回复消息段 |
| `forward_segments` | 所有转发消息段 |
| `message_events` | 所有消息事件 |

## 运行测试

```bash
# 运行所有测试
uv run pytest test/core/event/ -v

# 运行特定模块的测试
uv run pytest test/core/event/test_primitives.py -v

# 运行特定测试类
uv run pytest test/core/event/test_base.py::TestMessageSegmentBase -v

# 运行带覆盖率的测试
uv run pytest test/core/event/ --cov=ncatbot.core.event.message_event.types
```

## 测试分类

### 单元测试

每个模块都有对应的测试文件，测试内容包括：

- **创建测试** - 验证对象能正确创建
- **序列化测试** - 验证 `to_dict()` 方法
- **反序列化测试** - 验证 `from_dict()` 方法
- **往返测试** - 验证序列化后反序列化能得到相同结果
- **验证测试** - 验证字段验证逻辑（如 `At.qq` 必须是数字或 "all"）

### 集成测试

`test_integration.py` 包含：

- **完整消息解析** - 测试解析包含多种类型的完整消息
- **类型注册** - 验证所有类型都正确注册到 `TYPE_MAP`
- **边缘情况** - 空消息、Unicode、特殊字符等

### 真实数据测试

使用 `TestWithRealData` 和 `TestPrimitivesWithRealData` 等类，用真实的日志数据进行测试。这些测试会在数据不可用时自动跳过。

## 扩展测试

### 添加新的消息类型测试

1. 在对应的测试文件中添加新的测试类
2. 参考现有测试结构编写测试用例
3. 如果需要，在 `conftest.py` 中添加新的 fixture

### 添加新的测试数据

1. 将新的日志行或事件数据添加到 `data.txt`
2. 或创建新的 `.txt` 文件（会自动加载）
3. 运行测试验证数据能正确解析

## 注意事项

- 测试数据中的省略内容（如 `[...]`）会被自动处理
- 支持 Python 格式（单引号）和 JSON 格式（双引号）的数据
- 某些测试在没有对应类型数据时会自动跳过
