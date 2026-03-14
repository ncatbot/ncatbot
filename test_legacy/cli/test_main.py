"""CLI 主入口单元测试"""

import os
import sys
from unittest.mock import MagicMock, patch

import pytest


class TestParseArgs:
    """命令行参数解析测试"""

    def test_parse_args_empty(self):
        """测试无参数"""
        with patch.object(sys, "argv", ["ncatbot"]):
            from ncatbot.cli.main import parse_args

            args = parse_args()

            assert args.command is None
            assert args.args == []
            assert args.work_dir is None
            assert args.debug is False
            assert args.version is False

    def test_parse_args_command(self):
        """测试命令参数"""
        with patch.object(sys, "argv", ["ncatbot", "-c", "start"]):
            from ncatbot.cli.main import parse_args

            args = parse_args()

            assert args.command == "start"

    def test_parse_args_with_args(self):
        """测试带参数的命令"""
        with patch.object(
            sys, "argv", ["ncatbot", "-c", "install", "-a", "plugin1", "plugin2"]
        ):
            from ncatbot.cli.main import parse_args

            args = parse_args()

            assert args.command == "install"
            assert args.args == ["plugin1", "plugin2"]

    def test_parse_args_work_dir(self):
        """测试工作目录参数"""
        with patch.object(sys, "argv", ["ncatbot", "-w", "/tmp/test"]):
            from ncatbot.cli.main import parse_args

            args = parse_args()

            assert args.work_dir == "/tmp/test"

    def test_parse_args_debug(self):
        """测试调试模式"""
        with patch.object(sys, "argv", ["ncatbot", "-d"]):
            from ncatbot.cli.main import parse_args

            args = parse_args()

            assert args.debug is True

    def test_parse_args_version(self):
        """测试版本参数"""
        with patch.object(sys, "argv", ["ncatbot", "--version"]):
            from ncatbot.cli.main import parse_args

            args = parse_args()

            assert args.version is True


class TestSetupWorkDirectory:
    """工作目录设置测试"""

    def test_setup_work_directory_default(self, tmp_path):
        """测试默认工作目录"""
        os.chdir(tmp_path)

        from ncatbot.cli.main import setup_work_directory

        setup_work_directory()

        assert os.getcwd() == str(tmp_path)

    def test_setup_work_directory_custom(self, tmp_path):
        """测试自定义工作目录"""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()

        from ncatbot.cli.main import setup_work_directory

        setup_work_directory(str(custom_dir))

        assert os.getcwd() == str(custom_dir)

    def test_setup_work_directory_not_exist(self):
        """测试不存在的工作目录"""
        from ncatbot.cli.main import setup_work_directory

        with pytest.raises(FileNotFoundError):
            setup_work_directory("/nonexistent/path")


class TestHandleCommandMode:
    """命令模式处理测试"""

    def test_handle_command_mode_success(self):
        """测试成功执行命令"""
        mock_args = MagicMock()
        mock_args.command = "help"
        mock_args.args = []

        with patch("ncatbot.cli.main.registry") as mock_registry:
            from ncatbot.cli.main import handle_command_mode

            handle_command_mode(mock_args)

            mock_registry.execute.assert_called_once_with("help")

    def test_handle_command_mode_with_args(self):
        """测试带参数的命令执行"""
        mock_args = MagicMock()
        mock_args.command = "create"
        mock_args.args = ["my_plugin"]

        with patch("ncatbot.cli.main.registry") as mock_registry:
            from ncatbot.cli.main import handle_command_mode

            handle_command_mode(mock_args)

            mock_registry.execute.assert_called_once_with("create", "my_plugin")

    def test_handle_command_mode_error(self):
        """测试命令执行错误"""
        mock_args = MagicMock()
        mock_args.command = "error_cmd"
        mock_args.args = []

        with (
            patch("ncatbot.cli.main.registry") as mock_registry,
            pytest.raises(SystemExit),
        ):
            mock_registry.execute.side_effect = Exception("Command failed")

            from ncatbot.cli.main import handle_command_mode

            handle_command_mode(mock_args)


class TestHandleInteractiveMode:
    """交互模式处理测试"""

    def test_handle_interactive_mode_exit(self, capsys):
        """测试交互模式退出"""
        from ncatbot.cli.utils import CLIExit

        with (
            patch("builtins.input", side_effect=["q"]),
            patch("ncatbot.cli.main.registry") as mock_registry,
        ):
            mock_registry.execute.side_effect = CLIExit()

            from ncatbot.cli.main import handle_interactive_mode

            handle_interactive_mode()

    def test_handle_interactive_mode_keyboard_interrupt(self, capsys):
        """测试 Ctrl+C 退出"""
        with patch("builtins.input", side_effect=KeyboardInterrupt()):
            from ncatbot.cli.main import handle_interactive_mode

            handle_interactive_mode()

            captured = capsys.readouterr()
            assert "再见" in captured.out

    def test_handle_interactive_mode_empty_input(self):
        """测试空输入"""
        from ncatbot.cli.utils import CLIExit

        with (
            patch("builtins.input", side_effect=["", "q"]),
            patch("ncatbot.cli.main.registry") as mock_registry,
        ):
            # 第一次空输入不调用 execute，第二次 q 调用并抛出 CLIExit
            mock_registry.execute.side_effect = CLIExit()

            from ncatbot.cli.main import handle_interactive_mode

            handle_interactive_mode()

            # execute 只被调用一次（空输入被跳过）
            assert mock_registry.execute.call_count == 1


class TestMain:
    """主函数测试"""

    def test_main_version(self, capsys):
        """测试版本显示"""
        mock_dist = MagicMock()
        mock_dist.version = "1.0.0"

        with (
            patch.object(sys, "argv", ["ncatbot", "--version"]),
            patch("pkg_resources.get_distribution", return_value=mock_dist),
            patch("ncatbot.cli.main.config") as mock_config,
        ):
            mock_config.bot_uin = "123456789"

            from ncatbot.cli.main import main

            main()

            captured = capsys.readouterr()
            assert "1.0.0" in captured.out

    def test_main_invalid_work_dir(self, capsys):
        """测试无效工作目录"""
        with (
            patch.object(sys, "argv", ["ncatbot", "-w", "/nonexistent/path"]),
            pytest.raises(SystemExit),
        ):
            from ncatbot.cli.main import main

            main()
