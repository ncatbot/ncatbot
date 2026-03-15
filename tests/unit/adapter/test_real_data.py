"""
数据驱动事件解析测试 — 使用真实 OB11 数据

来源: test_legacy/core/event/ (TestDataProvider + 真实 OB11 数据文件)

数据来源优先级:
  1. 环境变量 NCATBOT_TEST_DATA_FILE 指定的文件路径
  2. 默认路径 dev/data.txt

文件格式: 每行一条 JSON/Python-dict，包含 post_type 字段即为有效事件。
无数据文件时所有测试自动 pytest.skip。

规范:
  RD-01: 所有事件可被 EventParser.parse() 成功解析
  RD-02: 所有消息事件的 message 段可被 parse_segment() 逐个解析
  RD-03: 解析后的事件类型与 post_type 对应
"""

import ast
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest

from ncatbot.adapter.napcat.parser import EventParser
from ncatbot.types import BaseEventData
from ncatbot.types.segment.base import parse_segment


# ── 数据文件发现 ──────────────────────────────────────────────

DEFAULT_DATA_FILE = "dev/data.txt"
DATA_FILE_ENV_VAR = "NCATBOT_TEST_DATA_FILE"


def _find_project_root() -> Path:
    current = Path(__file__).resolve().parent
    while current != current.parent:
        if (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path(__file__).resolve().parent.parent.parent.parent


def _resolve_data_file() -> Optional[Path]:
    root = _find_project_root()
    env_path = os.environ.get(DATA_FILE_ENV_VAR)
    if env_path:
        p = Path(env_path) if Path(env_path).is_absolute() else root / env_path
        if p.exists():
            return p
    default = root / DEFAULT_DATA_FILE
    return default if default.exists() else None


# ── 数据加载 ──────────────────────────────────────────────────


def _parse_event_str(s: str) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        pass
    try:
        return ast.literal_eval(s)
    except (ValueError, SyntaxError):
        return None


def _extract_dict(text: str, start: int) -> Optional[str]:
    depth = 0
    in_str = False
    esc = False
    for i in range(start, len(text)):
        c = text[i]
        if esc:
            esc = False
            continue
        if c == "\\":
            esc = True
            continue
        if c in ('"', "'") and not in_str:
            in_str = True
        elif c in ('"', "'") and in_str:
            in_str = False
        elif c == "{" and not in_str:
            depth += 1
        elif c == "}" and not in_str:
            depth -= 1
            if depth == 0:
                return text[start : i + 1]
    return None


def load_events(path: Path) -> List[Dict[str, Any]]:
    events = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            idx = line.find("{")
            if idx == -1:
                continue
            ds = _extract_dict(line, idx)
            if ds:
                ev = _parse_event_str(ds)
                if ev and isinstance(ev, dict) and "post_type" in ev:
                    events.append(ev)
    return events


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="module")
def real_events() -> List[Dict[str, Any]]:
    path = _resolve_data_file()
    if not path:
        pytest.skip(
            f"真实数据文件不可用。设置 {DATA_FILE_ENV_VAR} 环境变量或确保 {DEFAULT_DATA_FILE} 存在"
        )
    events = load_events(path)
    if not events:
        pytest.skip("数据文件中没有有效事件")
    return events


@pytest.fixture(scope="module")
def message_events(real_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    msgs = [e for e in real_events if e.get("post_type") == "message"]
    if not msgs:
        pytest.skip("数据文件中没有消息事件")
    return msgs


# ── RD-01: 全量事件解析 ──────────────────────────────────────


class TestRealEventParsing:
    """RD-01: 数据文件中每一条事件都能被 EventParser 成功解析"""

    def test_all_events_parseable(self, real_events: List[Dict[str, Any]]):
        failed = []
        for i, ev in enumerate(real_events):
            try:
                result = EventParser.parse(ev)
                assert isinstance(result, BaseEventData)
            except Exception as exc:
                failed.append((i, ev.get("post_type"), str(exc)[:80]))
        assert not failed, f"解析失败 {len(failed)}/{len(real_events)} 条: {failed[:5]}"


# ── RD-02: 消息段逐个解析 ────────────────────────────────────


class TestRealSegmentParsing:
    """RD-02: 消息事件中的每个 segment 都能被 parse_segment() 解析"""

    def test_all_segments_parseable(self, message_events: List[Dict[str, Any]]):
        total = 0
        failed = []
        for ev in message_events:
            for seg in ev.get("message", []):
                total += 1
                try:
                    parse_segment(seg)
                except Exception as exc:
                    failed.append((seg.get("type"), str(exc)[:60]))
        assert total > 0, "没有找到消息段"
        assert not failed, f"解析失败 {len(failed)}/{total} 段: {failed[:5]}"


# ── RD-03: post_type 一致性 ──────────────────────────────────


class TestRealEventTypeConsistency:
    """RD-03: 解析后的 post_type 与原始数据一致"""

    def test_post_type_matches(self, real_events: List[Dict[str, Any]]):
        for ev in real_events:
            result = EventParser.parse(ev)
            raw_pt = ev["post_type"]
            # message_sent 映射为 message
            expected = "message" if raw_pt == "message_sent" else raw_pt
            assert result.post_type.value == expected, (
                f"期望 post_type={expected}, 实际 {result.post_type.value}"
            )
