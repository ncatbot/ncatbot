"""事件日志格式配置验证。"""

import pytest
from ncatbot.utils.config.models import LoggingConfig


class TestEventLogFormatConfig:
    """ELF-01 ~ ELF-04: event_log_format 配置字段验证"""

    def test_default_is_summary(self):
        """ELF-01: 默认值为 summary"""
        cfg = LoggingConfig()
        assert cfg.event_log_format == "summary"

    def test_accepts_raw(self):
        """ELF-02: 接受 raw"""
        cfg = LoggingConfig(event_log_format="raw")
        assert cfg.event_log_format == "raw"

    def test_accepts_summary(self):
        """ELF-03: 接受 summary"""
        cfg = LoggingConfig(event_log_format="summary")
        assert cfg.event_log_format == "summary"

    def test_rejects_invalid_value(self):
        """ELF-04: 拒绝非法值"""
        with pytest.raises(ValueError, match="event_log_format"):
            LoggingConfig(event_log_format="fancy")

    def test_case_insensitive_raw(self):
        """ELF-05: 大写 RAW 被归一化为 raw"""
        cfg = LoggingConfig(event_log_format="RAW")
        assert cfg.event_log_format == "raw"

    def test_case_insensitive_summary(self):
        """ELF-06: 大写 SUMMARY 被归一化为 summary"""
        cfg = LoggingConfig(event_log_format="SUMMARY")
        assert cfg.event_log_format == "summary"
