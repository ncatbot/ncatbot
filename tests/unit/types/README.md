# Types 模块测试

源码模块: `ncatbot.types`

## 验证规范

### 事件数据类型 (`test_types.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| T-01 | BaseEventData ID 强转 | `int` 类型的 `self_id`、`user_id` 自动转为 `str` |
| T-02 | GroupMessageEventData | 必须包含 `group_id` 字段 |
| T-03 | PrivateMessageEventData | 不含 `group_id` 字段 |
| T-04 | NoticeEventData 子类 | 各子类包含对应 `notice_type` |
| T-05 | RequestEventData 子类 | 各子类包含 `flag` 字段 |

### 消息段体系 (`test_segments.py`)

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| T-10 | `to_dict()` 输出格式 | 输出符合 OB11 `{"type": ..., "data": {...}}` 格式 |
| T-11 | `parse_segment()` 反序列化 | 从 dict 正确还原为 Segment 实例 |
| T-12 | 类型注册机制 | `SEGMENT_MAP` 包含所有内置类型，自定义类型可注册 |
| T-13 | MessageArray 链式构造 | `append()` 链式调用，`__len__`、`__iter__` 正确 |
| T-14 | Segment 子类字段校验 | `At` 必须有 `qq` 字段，`Image` 必须有 `file` 等 |

### parse_segment 直接解析 (`test_segment_parsing.py`)

使用 `parse_segment()` 直接解析 OB11 `{"type": ..., "data": {...}}` 格式。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| S-01 | 文本段解析 | text / Unicode / 空 |
| S-02 | face 段 id 强转 | `int` → `str` |
| S-03 | at 段 | qq 数字 / "all" / int 自动转 |
| S-04 | reply 段 | id 强转 |
| S-05 | image 段 | 必填 file + 可选 url/sub_type |
| S-06 | record/video/file 段 | DownloadableSegment 子类 |
| S-07 | 未知类型 | 抛 `ValueError` |
| S-08 | 序列化/反序列化往返 | `parse_segment → to_dict → parse_segment` 一致 |
| S-09 | extra="allow" 容错 | 额外字段不报错，缺必填字段抛异常 |
| S-10 | SEGMENT_MAP 完整性 | 包含所有 14 种内置类型 |

### CQ 码解析 (`test_cq_parser.py`)

测试 `parse_cq_code_to_onebot11()` 将 CQ 码字符串转为 OB11 消息数组。

| 规范 ID | 说明 | 验证点 |
|---------|------|--------|
| CQ-01 | 纯文本 | 无 CQ 码 → 单个 text 段 |
| CQ-02 | 单个 CQ 码 | `[CQ:at,qq=123]` → at 段 |
| CQ-03 | 混合 | 前后文本 + 中间 CQ 码 |
| CQ-04 | 多参数 | `[CQ:image,file=...,url=...]` |
| CQ-05 | 转义还原 | `&amp;` → `&`, `&#91;` → `[` 等 |
| CQ-06 | 无参数 | `[CQ:shake]` → data 为空 |
| CQ-07 | 连续 CQ 码 | 中间无 text 段 |
| CQ-08 | 空字符串 | → 空列表 |
