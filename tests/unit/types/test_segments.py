"""
消息段体系规范测试

规范:
  T-10: to_dict() 输出 OB11 格式
  T-11: parse_segment() 反序列化
  T-12: 类型注册机制
  T-13: MessageArray 链式构造
  T-14: 各 Segment 子类字段校验
"""

import pytest
from pydantic import ValidationError

from ncatbot.types.segment.base import parse_segment, SEGMENT_MAP
from ncatbot.types.segment.text import PlainText, Face, At, Reply
from ncatbot.types.segment.media import Image, Record, Video


# ---- T-10: to_dict() 输出 OB11 格式 ----


def test_plaintext_to_dict():
    """T-10: PlainText.to_dict() → {"type": "text", "data": {"text": ...}}"""
    seg = PlainText(text="hello world")
    d = seg.to_dict()
    assert d == {"type": "text", "data": {"text": "hello world"}}


def test_at_to_dict():
    """T-10: At.to_dict() → {"type": "at", "data": {"qq": ...}}"""
    seg = At(qq="12345")
    d = seg.to_dict()
    assert d["type"] == "at"
    assert d["data"]["qq"] == "12345"


def test_face_to_dict():
    """T-10: Face.to_dict() → {"type": "face", "data": {"id": ...}}"""
    seg = Face(id="123")
    d = seg.to_dict()
    assert d["type"] == "face"
    assert d["data"]["id"] == "123"


def test_image_to_dict():
    """T-10: Image.to_dict() → {"type": "image", "data": {"file": ...}}"""
    seg = Image(file="http://example.com/img.jpg")
    d = seg.to_dict()
    assert d["type"] == "image"
    assert d["data"]["file"] == "http://example.com/img.jpg"


# ---- T-11: parse_segment() 反序列化 ----


def test_parse_text_segment():
    """T-11: 从 dict 还原 PlainText"""
    seg = parse_segment({"type": "text", "data": {"text": "hi"}})
    assert isinstance(seg, PlainText)
    assert seg.text == "hi"


def test_parse_at_segment():
    """T-11: 从 dict 还原 At"""
    seg = parse_segment({"type": "at", "data": {"qq": "all"}})
    assert isinstance(seg, At)
    assert seg.qq == "all"


def test_parse_reply_segment():
    """T-11: 从 dict 还原 Reply"""
    seg = parse_segment({"type": "reply", "data": {"id": "42"}})
    assert isinstance(seg, Reply)
    assert seg.id == "42"


def test_parse_unknown_type_raises():
    """T-11 补充: 未知类型抛 ValueError"""
    with pytest.raises(ValueError, match="Unknown segment type"):
        parse_segment({"type": "unknown_segment", "data": {}})


# ---- T-12: 类型注册机制 ----


def test_segment_type_registration():
    """T-12: _type ClassVar 自动注册到 SEGMENT_MAP"""
    assert "text" in SEGMENT_MAP
    assert SEGMENT_MAP["text"] is PlainText
    assert "at" in SEGMENT_MAP
    assert SEGMENT_MAP["at"] is At
    assert "face" in SEGMENT_MAP
    assert SEGMENT_MAP["face"] is Face
    assert "image" in SEGMENT_MAP
    assert SEGMENT_MAP["image"] is Image
    assert "record" in SEGMENT_MAP
    assert SEGMENT_MAP["record"] is Record
    assert "video" in SEGMENT_MAP
    assert SEGMENT_MAP["video"] is Video


def test_parse_image_from_registered_type():
    """T-12 补充: parse_segment 使用注册表还原 Image"""
    seg = parse_segment({"type": "image", "data": {"file": "test.jpg"}})
    assert isinstance(seg, Image)
    assert seg.file == "test.jpg"


# ---- T-13: MessageArray ----


def test_message_array_from_list():
    """T-13: MessageArray.from_list 从 OB11 列表构造"""
    from ncatbot.types.segment.array import MessageArray

    arr = MessageArray.from_list(
        [
            {"type": "text", "data": {"text": "hi "}},
            {"type": "at", "data": {"qq": "123"}},
        ]
    )
    assert len(arr) == 2
    segments = list(arr)
    assert isinstance(segments[0], PlainText)
    assert isinstance(segments[1], At)


def test_message_array_iter():
    """T-13 补充: MessageArray 支持迭代"""
    from ncatbot.types.segment.array import MessageArray

    arr = MessageArray([PlainText(text="a"), PlainText(text="b")])
    texts = [seg.text for seg in arr]
    assert texts == ["a", "b"]


# ---- T-14: 各 Segment 子类字段校验 ----


def test_at_qq_all_valid():
    """T-14: At(qq="all") 合法"""
    seg = At(qq="all")
    assert seg.qq == "all"


def test_at_qq_digit_valid():
    """T-14: At(qq="12345") 合法"""
    seg = At(qq="12345")
    assert seg.qq == "12345"


def test_at_qq_invalid_raises():
    """T-14: At(qq="abc") 不合法"""
    with pytest.raises(ValidationError):
        At(qq="abc")


def test_face_id_coerces_int():
    """T-14: Face(id=123) 自动转 str"""
    seg = Face(id=123)
    assert seg.id == "123"


def test_reply_id_coerces_int():
    """T-14: Reply(id=42) 自动转 str"""
    seg = Reply(id=42)
    assert seg.id == "42"


def test_image_optional_fields():
    """T-14: Image 的可选字段可以为 None"""
    seg = Image(file="test.jpg")
    assert seg.url is None
    assert seg.file_id is None
