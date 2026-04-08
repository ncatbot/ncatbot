"""事件日志摘要格式化。

测试 format_event_summary() 纯函数：
- 输入为 dict（raw event data），不依赖具体数据模型类
- 按 post_type 分发到不同格式模板
"""

import logging
from unittest.mock import patch, MagicMock

import pytest
from ncatbot.utils.logger.event_log import format_event_summary


class TestFormatGroupMessage:
    """ELS-01 ~ ELS-03: 群消息摘要格式"""

    def test_group_message_full(self):
        """ELS-01: 群消息含 group_name 和 nickname"""
        data = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "626192977",
            "group_name": "测试群",
            "user_id": "2663646956",
            "sender": {"nickname": "张三", "user_id": "2663646956"},
            "raw_message": "你好世界",
        }
        result = format_event_summary(data)
        assert result == "[群消息] 测试群(626192977) 张三(2663646956): 你好世界"

    def test_group_message_no_group_name(self):
        """ELS-02: 群消息缺少 group_name 时降级"""
        data = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "626192977",
            "user_id": "2663646956",
            "sender": {"nickname": "张三"},
            "raw_message": "你好",
        }
        result = format_event_summary(data)
        assert result == "[群消息] 626192977 张三(2663646956): 你好"

    def test_group_message_long_raw_message_truncated(self):
        """ELS-03: raw_message 超过 100 字符被截断"""
        long_msg = "A" * 150
        data = {
            "post_type": "message",
            "message_type": "group",
            "group_id": "123",
            "group_name": "G",
            "user_id": "456",
            "sender": {"nickname": "U"},
            "raw_message": long_msg,
        }
        result = format_event_summary(data)
        assert result == f"[群消息] G(123) U(456): {'A' * 100}..."
        assert len(result.split(": ", 1)[1]) == 103  # 100 + "..."


class TestFormatPrivateMessage:
    """ELS-04 ~ ELS-05: 私聊消息摘要格式"""

    def test_private_message(self):
        """ELS-04: 私聊消息标准格式"""
        data = {
            "post_type": "message",
            "message_type": "private",
            "user_id": "100000004",
            "sender": {"nickname": "TestUser"},
            "raw_message": "/like 3051561876",
        }
        result = format_event_summary(data)
        assert result == "[私聊消息] TestUser(100000004): /like 3051561876"

    def test_private_message_no_nickname(self):
        """ELS-05: 缺少 nickname 降级显示 user_id"""
        data = {
            "post_type": "message",
            "message_type": "private",
            "user_id": "100000004",
            "sender": {},
            "raw_message": "hello",
        }
        result = format_event_summary(data)
        assert result == "[私聊消息] 100000004: hello"


class TestFormatNotice:
    """ELS-06 ~ ELS-08: 通知事件摘要格式"""

    def test_notice_with_group(self):
        """ELS-06: 通知事件含 group_id"""
        data = {
            "post_type": "notice",
            "notice_type": "group_recall",
            "group_id": "100000006",
            "user_id": "100000007",
        }
        result = format_event_summary(data)
        assert result == "[通知] group_recall 群:100000006 用户:100000007"

    def test_notice_without_group(self):
        """ELS-07: 通知事件无 group_id"""
        data = {
            "post_type": "notice",
            "notice_type": "friend_add",
            "user_id": "100000007",
        }
        result = format_event_summary(data)
        assert result == "[通知] friend_add 用户:100000007"

    def test_notice_poke_with_sub_type(self):
        """ELS-08: notify 类型含 sub_type"""
        data = {
            "post_type": "notice",
            "notice_type": "notify",
            "sub_type": "poke",
            "group_id": "100000005",
            "user_id": "100000004",
            "target_id": "100000001",
        }
        result = format_event_summary(data)
        assert result == "[通知] notify.poke 群:100000005 用户:100000004"


class TestFormatRequest:
    """ELS-09 ~ ELS-10: 请求事件摘要格式"""

    def test_friend_request(self):
        """ELS-09: 好友请求"""
        data = {
            "post_type": "request",
            "request_type": "friend",
            "user_id": "100000004",
        }
        result = format_event_summary(data)
        assert result == "[请求] friend 用户:100000004"

    def test_group_request_with_group(self):
        """ELS-10: 入群请求含 group_id"""
        data = {
            "post_type": "request",
            "request_type": "group",
            "user_id": "100000004",
            "group_id": "100000005",
        }
        result = format_event_summary(data)
        assert result == "[请求] group 群:100000005 用户:100000004"


class TestFormatMetaEvent:
    """ELS-11: 元事件摘要格式"""

    def test_heartbeat(self):
        """ELS-11: 元事件标准格式"""
        data = {
            "post_type": "meta_event",
            "meta_event_type": "heartbeat",
        }
        result = format_event_summary(data)
        assert result == "[元事件] heartbeat"


class TestFormatUnknown:
    """ELS-12 ~ ELS-13: 未知/降级格式"""

    def test_unknown_post_type(self):
        """ELS-12: 未知 post_type 降级显示"""
        data = {
            "post_type": "some_new_type",
            "foo": "bar",
        }
        result = format_event_summary(data)
        assert result.startswith("[事件] some_new_type: ")

    def test_message_sent_uses_message_format(self):
        """ELS-13: message_sent 复用消息格式"""
        data = {
            "post_type": "message_sent",
            "message_type": "group",
            "group_id": "123",
            "group_name": "G",
            "user_id": "456",
            "sender": {"nickname": "Bot"},
            "raw_message": "hi",
        }
        result = format_event_summary(data)
        assert result == "[群消息] G(123) Bot(456): hi"


class TestOnEventLogFormat:
    """ELS-14 ~ ELS-17: NapCatAdapter._on_event 日志格式集成"""

    def _make_adapter(self):
        """创建一个最小化的 NapCatAdapter 用于测试 _on_event"""
        from ncatbot.adapter.napcat.adapter import NapCatAdapter
        from ncatbot.adapter.napcat.parser import NapCatEventParser

        adapter = NapCatAdapter.__new__(NapCatAdapter)
        adapter._event_callback = None
        adapter._parser = NapCatEventParser()
        return adapter

    def _make_raw_data(self):
        return {
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "group_id": "123",
            "group_name": "TestGroup",
            "user_id": "456",
            "sender": {"user_id": "456", "nickname": "Nick"},
            "raw_message": "hello",
            "message": [{"type": "text", "data": {"text": "hello"}}],
            "message_id": "789",
            "time": 1000000000,
            "self_id": "111",
            "font": 14,
        }

    @pytest.mark.asyncio
    async def test_summary_format_logs_summary(self):
        """ELS-14: event_log_format=summary 时以 resolved level 输出摘要"""
        adapter = self._make_adapter()
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {}
        mock_cfg.config.logging.event_log_format = "summary"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(self._make_raw_data())
                calls = mock_log._log.call_args_list
                assert len(calls) >= 1
                summary_msg = calls[0][0][1]
                assert "[群消息]" in summary_msg
                assert "TestGroup(123)" in summary_msg

    @pytest.mark.asyncio
    async def test_summary_format_emits_debug_raw(self):
        """ELS-15: event_log_format=summary 时 DEBUG 级别额外输出完整 JSON"""
        adapter = self._make_adapter()
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {}
        mock_cfg.config.logging.event_log_format = "summary"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(self._make_raw_data())
                calls = mock_log._log.call_args_list
                assert len(calls) == 2
                debug_level = calls[1][0][0]
                assert debug_level == logging.DEBUG

    @pytest.mark.asyncio
    async def test_raw_format_logs_json(self):
        """ELS-16: event_log_format=raw 时输出完整 JSON（旧行为）"""
        adapter = self._make_adapter()
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {}
        mock_cfg.config.logging.event_log_format = "raw"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(self._make_raw_data())
                calls = mock_log._log.call_args_list
                assert len(calls) == 1
                msg = calls[0][0][1]
                assert "收到事件 message:" in msg

    @pytest.mark.asyncio
    async def test_none_level_suppresses_all(self):
        """ELS-17: event_log_levels=NONE 时 summary 和 raw 都不输出"""
        adapter = self._make_adapter()
        mock_cfg = MagicMock()
        mock_cfg.config.logging.event_log_levels = {"message": "NONE"}
        mock_cfg.config.logging.event_log_format = "summary"

        with patch("ncatbot.adapter.napcat.adapter.get_config_manager", return_value=mock_cfg):
            with patch("ncatbot.adapter.napcat.adapter.LOG") as mock_log:
                await adapter._on_event(self._make_raw_data())
                mock_log._log.assert_not_called()
