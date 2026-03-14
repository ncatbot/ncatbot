"""系统命令单元测试"""

from unittest.mock import MagicMock, patch

import pytest

from ncatbot.cli.utils import CLIExit


class TestStart:
    """start 命令测试"""

    def test_start_creates_client(self, capsys):
        """测试启动命令创建客户端"""
        mock_client = MagicMock()

        with patch("ncatbot.core.BotClient", return_value=mock_client):
            from ncatbot.cli.commands.system_commands import start

            start()

            mock_client.run.assert_called_once()

    def test_start_handles_error(self, capsys):
        """测试启动失败时的错误处理"""
        with patch(
            "ncatbot.core.BotClient",
            side_effect=Exception("Connection failed"),
        ):
            from ncatbot.cli.commands.system_commands import start

            start()

            captured = capsys.readouterr()
            assert "启动失败" in captured.out


class TestUpdate:
    """update 命令测试"""

    def test_update_success(self, capsys):
        """测试更新成功"""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stderr = ""

        with patch("subprocess.run", return_value=mock_result):
            from ncatbot.cli.commands.system_commands import update

            update()

            captured = capsys.readouterr()
            assert "更新成功" in captured.out

    def test_update_failure(self, capsys):
        """测试更新失败"""
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = "Package not found"

        with patch("subprocess.run", return_value=mock_result):
            from ncatbot.cli.commands.system_commands import update

            update()

            captured = capsys.readouterr()
            assert "更新失败" in captured.out

    def test_update_exception(self, capsys):
        """测试更新异常"""
        with patch("subprocess.run", side_effect=Exception("Network error")):
            from ncatbot.cli.commands.system_commands import update

            update()

            captured = capsys.readouterr()
            assert "出错" in captured.out


class TestExitCli:
    """exit_cli 命令测试"""

    def test_exit_raises_cli_exit(self, capsys):
        """测试退出命令抛出 CLIExit 异常"""
        from ncatbot.cli.commands.system_commands import exit_cli

        with pytest.raises(CLIExit):
            exit_cli()

        captured = capsys.readouterr()
        assert "再见" in captured.out
