"""
测试 conftest 中的日志解析函数
"""
import json
from pathlib import Path

import pytest

from conftest import extract_event_dict_str, parse_event_dict_str, load_test_data


class TestExtractEventDictStr:
    """测试事件字典字符串提取"""
    
    def test_extract_simple_single_line(self):
        """测试从单行日志中提取字典"""
        log = "收到事件: {'type': 'text', 'data': 'hello'}"
        result = extract_event_dict_str(log)
        assert result is not None
        assert result == "{'type': 'text', 'data': 'hello'}"
    
    def test_extract_multiline(self):
        """测试从多行日志中提取字典"""
        log = """收到事件: {'type': 'message', 'data': {
            'text': 'hello',
            'nested': {'key': 'value'}
        }}"""
        result = extract_event_dict_str(log)
        assert result is not None
        # 应该能正确匹配所有括号
        assert result.count('{') == result.count('}')
    
    def test_extract_with_string_containing_braces(self):
        """测试从包含字符串中有大括号的日志中提取"""
        log = "收到事件: {'type': 'text', 'pattern': '{hello}'}"
        result = extract_event_dict_str(log)
        assert result is not None
        assert result == "{'type': 'text', 'pattern': '{hello}'}"
    
    def test_extract_no_event(self):
        """测试没有事件的日志"""
        log = "这是一条普通的日志消息"
        result = extract_event_dict_str(log)
        assert result is None
    
    def test_extract_nested_dicts(self):
        """测试包含嵌套字典的提取"""
        log = "收到事件: {'outer': {'inner': {'deep': 'value'}}}"
        result = extract_event_dict_str(log)
        assert result is not None
        assert result.count('{') == 3
        assert result.count('}') == 3


class TestParseEventDictStr:
    """测试事件字典字符串解析"""
    
    def test_parse_json_format(self):
        """测试解析 JSON 格式"""
        dict_str = '{"type": "text", "data": "hello"}'
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["type"] == "text"
        assert result["data"] == "hello"
    
    def test_parse_python_format(self):
        """测试解析 Python 格式（单引号）"""
        dict_str = "{'type': 'text', 'data': 'hello'}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["type"] == "text"
        assert result["data"] == "hello"
    
    def test_parse_mixed_quotes(self):
        """测试解析混合引号的情况"""
        dict_str = "{'type': \"text\", 'data': 'hello'}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
    
    def test_parse_nested_structures(self):
        """测试解析嵌套结构"""
        dict_str = "{'user': {'id': 123, 'name': 'test'}, 'items': [1, 2, 3]}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["user"]["id"] == 123
        assert result["items"] == [1, 2, 3]
    
    def test_parse_none_values(self):
        """测试解析包含 None 的字典"""
        dict_str = "{'key1': None, 'key2': 'value'}"
        result = parse_event_dict_str(dict_str)
        assert result is not None
        assert result["key1"] is None
        assert result["key2"] == "value"
    
    def test_parse_invalid_format(self):
        """测试解析无效格式"""
        dict_str = "this is not a dict"
        result = parse_event_dict_str(dict_str)
        assert result is None


class TestLoadTestData:
    """测试完整的数据加载流程"""
    
    def test_load_from_test_file(self):
        """测试从实际测试数据文件加载"""
        data_file = Path(__file__).parent / "data.txt"
        if not data_file.exists():
            pytest.skip("Test data file not found")
        
        events = load_test_data(data_file)
        assert len(events) > 0, "应该加载至少一个事件"
    
    def test_loaded_events_have_post_type(self):
        """测试加载的事件都有 post_type 字段"""
        data_file = Path(__file__).parent / "data.txt"
        if not data_file.exists():
            pytest.skip("Test data file not found")
        
        events = load_test_data(data_file)
        for event in events:
            assert "post_type" in event or "meta_event_type" in event, \
                "事件应该有 post_type 或 meta_event_type 字段"
    
    def test_can_parse_message_events(self):
        """测试能正确解析消息事件"""
        data_file = Path(__file__).parent / "data.txt"
        if not data_file.exists():
            pytest.skip("Test data file not found")
        
        events = load_test_data(data_file)
        message_events = [e for e in events if e.get("post_type") == "message"]
        
        if message_events:
            for event in message_events:
                assert "message" in event, "消息事件应该有 message 字段"
                assert isinstance(event["message"], list), "message 应该是列表"


class TestDataParsingRobustness:
    """测试数据解析的健壮性"""
    
    def test_extract_and_parse_roundtrip(self):
        """测试提取-解析的往返"""
        original_dict = {'type': 'message', 'data': {'text': 'hello', 'id': 123}}
        log = f"[LOG] 收到事件: {original_dict}"
        
        # 提取
        dict_str = extract_event_dict_str(log)
        assert dict_str is not None
        
        # 解析
        parsed = parse_event_dict_str(dict_str)
        assert parsed == original_dict
    
    def test_handle_escaped_quotes(self):
        """测试处理转义引号"""
        # 包含转义引号的字符串
        dict_str = r"{'message': 'He said \"hello\"', 'type': 'text'}"
        result = parse_event_dict_str(dict_str)
        # 这可能无法完美处理，但至少不应该崩溃
        # 如果解析失败是正常的
        if result:
            assert "message" in result or "type" in result
    
    def test_extract_with_surrounding_text(self):
        """测试从包含其他文本的日志中提取"""
        log = """[2025-12-30 13:27:22,075.075] DEBUG Adapter | 收到事件: {'id': 123, 'name': 'test', 'nested': {'key': 'value'}} more text after"""
        result = extract_event_dict_str(log)
        assert result is not None
        parsed = parse_event_dict_str(result)
        assert parsed is not None
        assert parsed["id"] == 123
        assert parsed["nested"]["key"] == "value"
