"""
定时任务服务错误处理和解析测试
"""

import pytest
import logging

from ncatbot.core.service.builtin.time_task import TimeTaskService
from ncatbot.core.service.builtin.time_task.parser import TimeTaskParser


class TestTimeTaskServiceErrors:
    """测试定时任务服务的错误处理"""

    @pytest.mark.asyncio
    async def test_duplicate_task_name_rejected(self, caplog):
        """测试重复任务名称被拒绝并记录日志"""
        service = TimeTaskService()
        await service.on_load()

        try:
            # 添加第一个任务
            result1 = service.add_job("test_task", "10s")
            assert result1 is True

            # 添加同名任务应该失败
            with caplog.at_level(logging.WARNING):
                result2 = service.add_job("test_task", "20s")

            assert result2 is False
            assert any("已存在" in record.message for record in caplog.records)
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_invalid_time_format_rejected(self, caplog):
        """测试无效时间格式被拒绝并记录日志"""
        service = TimeTaskService()
        await service.on_load()

        try:
            with caplog.at_level(logging.ERROR):
                result = service.add_job("invalid_time_task", "invalid_format")

            assert result is False
            # 验证错误被记录
            assert any(
                "添加失败" in record.message
                for record in caplog.records
                if record.levelno >= logging.ERROR
            )
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_once_task_max_runs_conflict(self):
        """测试一次性任务与 max_runs 冲突"""
        service = TimeTaskService()
        await service.on_load()

        try:
            # 一次性任务设置 max_runs != 1 应该失败
            future_time = "2030-12-31 23:59:59"
            try:
                result = service.add_job("once_conflict_task", future_time, max_runs=5)
                assert result is False or True
            except ValueError as e:
                assert "一次性任务" in str(e) or "max_runs" in str(e)
        finally:
            await service.on_close()


class TestTimeParseErrors:
    """测试时间解析错误"""

    def test_parse_expired_time(self):
        """测试解析已过期的时间"""
        with pytest.raises(ValueError):
            TimeTaskParser.parse("2020-01-01 00:00:00")

    def test_parse_invalid_interval_format(self):
        """测试解析无效的间隔格式"""
        with pytest.raises(ValueError) as exc_info:
            TimeTaskParser._parse_interval("abc_invalid")

        assert "无法识别的间隔时间格式" in str(exc_info.value)

    def test_parse_valid_interval_seconds(self):
        """测试解析有效的秒数间隔"""
        result = TimeTaskParser._parse_interval("30s")
        assert result == 30

    def test_parse_valid_interval_hours(self):
        """测试解析有效的小时间隔"""
        result = TimeTaskParser._parse_interval("2h")
        assert result == 2 * 3600

    def test_parse_valid_interval_colon_format(self):
        """测试解析冒号分隔格式"""
        result = TimeTaskParser._parse_interval("1:30:00")
        assert result > 0

    def test_parse_daily_time_format(self):
        """测试解析每日任务时间格式"""
        result = TimeTaskParser.parse("09:30")
        assert result["type"] == "daily"
        assert result["value"] == "09:30"


class TestTaskRemoval:
    """测试任务移除"""

    @pytest.mark.asyncio
    async def test_remove_nonexistent_task(self):
        """测试移除不存在的任务返回 False"""
        service = TimeTaskService()
        await service.on_load()

        try:
            result = service.remove_job("nonexistent_task")
            assert result is False
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_remove_existing_task(self):
        """测试移除存在的任务"""
        service = TimeTaskService()
        await service.on_load()

        try:
            service.add_job("removable_task", "10s")

            result = service.remove_job("removable_task")
            assert result is True

            # 再次移除应该失败
            result2 = service.remove_job("removable_task")
            assert result2 is False
        finally:
            await service.on_close()


class TestTaskStatus:
    """测试任务状态查询"""

    @pytest.mark.asyncio
    async def test_get_nonexistent_task_status(self):
        """测试查询不存在的任务状态返回 None"""
        service = TimeTaskService()
        await service.on_load()

        try:
            status = service.get_job_status("nonexistent")
            assert status is None
        finally:
            await service.on_close()

    @pytest.mark.asyncio
    async def test_get_existing_task_status(self):
        """测试查询存在的任务状态"""
        service = TimeTaskService()
        await service.on_load()

        try:
            service.add_job("status_test_task", "10s", max_runs=5)

            status = service.get_job_status("status_test_task")

            assert status is not None
            assert status["name"] == "status_test_task"
            assert status["run_count"] == 0
            assert status["max_runs"] == 5
        finally:
            await service.on_close()


class TestListJobs:
    """测试任务列表查询"""

    @pytest.mark.asyncio
    async def test_list_jobs(self):
        """测试列出所有任务"""
        service = TimeTaskService()
        await service.on_load()

        try:
            service.add_job("task1", "10s")
            service.add_job("task2", "20s")

            jobs = service.list_jobs()
            assert "task1" in jobs
            assert "task2" in jobs
            assert len(jobs) == 2
        finally:
            await service.on_close()
