"""
pytest 配置文件，提供测试夹具和数据加载器
"""
import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List

import pytest


def extract_event_dict_str(log_content: str) -> str | None:
    """从日志内容中提取事件字典字符串
    
    处理可能跨越多行的 JSON/Dict 结构，
    匹配 "收到事件: {...}" 格式，返回大括号内的完整内容
    """
    # 查找日志前缀
    match = re.search(r"收到事件: (\{)", log_content)
    if not match:
        return None
    
    # 找到第一个 { 的位置
    start_pos = match.start(1)
    
    # 从该位置开始，计算括号匹配，找到对应的 }
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(log_content)):
        char = log_content[i]
        
        if escape_next:
            escape_next = False
            continue
        
        if char == '\\':
            escape_next = True
            continue
        
        if char == '"' and not in_string:
            in_string = True
        elif char == '"' and in_string:
            in_string = False
        elif char == "'" and not in_string:
            in_string = True
        elif char == "'" and in_string:
            in_string = False
        elif char == '{' and not in_string:
            brace_count += 1
        elif char == '}' and not in_string:
            brace_count -= 1
            if brace_count == 0:
                return log_content[start_pos:i+1]
    
    return None


def parse_event_dict_str(data_str: str) -> Dict[str, Any] | None:
    """解析事件字典字符串
    
    支持两种格式:
    1. 标准 JSON 格式（双引号）
    2. Python repr 格式（单引号）
    """
    # 首先尝试标准 JSON 解析
    try:
        return json.loads(data_str)
    except json.JSONDecodeError:
        pass
    
    # 如果失败，尝试使用 ast.literal_eval 解析 Python 格式
    try:
        return ast.literal_eval(data_str)
    except (ValueError, SyntaxError):
        pass
    
    return None


def load_test_data(data_file: Path) -> List[Dict[str, Any]]:
    """加载测试数据文件，支持多行日志格式
    
    读取整个文件，按 "收到事件:" 标记分割事件，
    然后解析每个事件的字典数据
    """
    events = []
    
    with open(data_file, "r", encoding="utf-8") as f:
        content = f.read()
    
    # 按 "收到事件:" 分割，但保留它作为前缀用于识别
    # 找到所有 "收到事件:" 的位置
    pattern = r"收到事件:"
    matches = list(re.finditer(pattern, content))
    
    # 对每个匹配，提取从该位置到下一个日志起始的内容
    for i, match in enumerate(matches):
        start = match.start()
        
        # 确定结束位置：下一个日志的开始（通常以 [ 开头）
        # 或者文件末尾
        if i < len(matches) - 1:
            # 找到下一个 "收到事件:" 前最后一个日志行的开始
            next_start = matches[i + 1].start()
            # 向后查找最后一个换行符
            end = content.rfind('\n', start, next_start)
            if end == -1:
                end = next_start
        else:
            end = len(content)
        
        # 从 start 到 end 的内容
        log_section = content[start:end]
        
        # 从该部分提取事件字典字符串
        dict_str = extract_event_dict_str(log_section)
        if dict_str:
            event = parse_event_dict_str(dict_str)
            if event:
                events.append(event)
    
    return events


class TestDataProvider:
    """测试数据提供器，按类型分类存储事件数据"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self._events: List[Dict[str, Any]] = []
        self._message_events: List[Dict[str, Any]] = []
        self._meta_events: List[Dict[str, Any]] = []
        self._segments_by_type: Dict[str, List[Dict[str, Any]]] = {}
        self._load_all_data()
    
    def _load_all_data(self):
        """加载 data_dir 下所有 .txt 文件的测试数据"""
        for txt_file in self.data_dir.glob("*.txt"):
            events = load_test_data(txt_file)
            self._events.extend(events)
        
        # 分类事件
        for event in self._events:
            post_type = event.get("post_type")
            if post_type == "message":
                self._message_events.append(event)
                # 提取消息段
                for seg in event.get("message", []):
                    seg_type = seg.get("type")
                    if seg_type:
                        if seg_type not in self._segments_by_type:
                            self._segments_by_type[seg_type] = []
                        self._segments_by_type[seg_type].append(seg)
            elif post_type == "meta_event":
                self._meta_events.append(event)
    
    @property
    def all_events(self) -> List[Dict[str, Any]]:
        """获取所有事件"""
        return self._events
    
    @property
    def message_events(self) -> List[Dict[str, Any]]:
        """获取所有消息事件"""
        return self._message_events
    
    @property
    def meta_events(self) -> List[Dict[str, Any]]:
        """获取所有元事件"""
        return self._meta_events
    
    def get_segments_by_type(self, seg_type: str) -> List[Dict[str, Any]]:
        """获取指定类型的消息段"""
        return self._segments_by_type.get(seg_type, [])
    
    @property
    def available_segment_types(self) -> List[str]:
        """获取所有可用的消息段类型"""
        return list(self._segments_by_type.keys())
    
    def get_all_segments(self) -> List[Dict[str, Any]]:
        """获取所有消息段"""
        all_segments = []
        for segments in self._segments_by_type.values():
            all_segments.extend(segments)
        return all_segments


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """测试数据目录"""
    return Path(__file__).parent


@pytest.fixture(scope="session")
def data_provider(test_data_dir: Path) -> TestDataProvider:
    """测试数据提供器"""
    return TestDataProvider(test_data_dir)


@pytest.fixture
def text_segments(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """文本消息段数据"""
    return data_provider.get_segments_by_type("text")


@pytest.fixture
def image_segments(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """图片消息段数据"""
    return data_provider.get_segments_by_type("image")


@pytest.fixture
def face_segments(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """表情消息段数据"""
    return data_provider.get_segments_by_type("face")


@pytest.fixture
def at_segments(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """@消息段数据"""
    return data_provider.get_segments_by_type("at")


@pytest.fixture
def reply_segments(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """引用回复消息段数据"""
    return data_provider.get_segments_by_type("reply")


@pytest.fixture
def forward_segments(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """转发消息段数据"""
    return data_provider.get_segments_by_type("forward")


@pytest.fixture
def message_events(data_provider: TestDataProvider) -> List[Dict[str, Any]]:
    """消息事件数据"""
    return data_provider.message_events
