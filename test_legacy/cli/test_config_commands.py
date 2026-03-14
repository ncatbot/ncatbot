"""配置命令单元测试"""

from unittest.mock import patch


class TestSetQQ:
    """set_qq 命令测试"""

    def test_set_qq_with_argument(self, mock_config):
        """测试直接传入 QQ 号"""
        with (
            patch("ncatbot.cli.commands.config_commands.config", mock_config),
            patch("builtins.input", side_effect=["123456789"]),
        ):
            from ncatbot.cli.commands.config_commands import set_qq

            result = set_qq("123456789")

            assert result == "123456789"
            assert mock_config.bot_uin == "123456789"
            mock_config.save.assert_called_once()

    def test_set_qq_interactive(self, mock_config):
        """测试交互式输入 QQ 号"""
        with (
            patch("ncatbot.cli.commands.config_commands.config", mock_config),
            patch("builtins.input", side_effect=["987654321", "987654321"]),
        ):
            from ncatbot.cli.commands.config_commands import set_qq

            result = set_qq()

            assert result == "987654321"
            assert mock_config.bot_uin == "987654321"

    def test_set_qq_invalid_input(self, mock_config, capsys):
        """测试非数字输入"""
        with (
            patch("ncatbot.cli.commands.config_commands.config", mock_config),
            patch("builtins.input", side_effect=["abc", "123456789", "123456789"]),
        ):
            from ncatbot.cli.commands.config_commands import set_qq

            result = set_qq()

            captured = capsys.readouterr()
            assert "必须为数字" in captured.out
            assert result == "123456789"

    def test_set_qq_mismatch_confirmation(self, mock_config, capsys):
        """测试确认不匹配"""
        with (
            patch("ncatbot.cli.commands.config_commands.config", mock_config),
            patch(
                "builtins.input",
                side_effect=["123456789", "987654321", "123456789", "123456789"],
            ),
        ):
            from ncatbot.cli.commands.config_commands import set_qq

            result = set_qq()

            captured = capsys.readouterr()
            assert "不一致" in captured.out
            assert result == "123456789"


class TestSetRoot:
    """set_root 命令测试"""

    def test_set_root_with_argument(self, mock_config):
        """测试直接传入管理员 QQ 号"""
        with patch("ncatbot.cli.commands.config_commands.config", mock_config):
            from ncatbot.cli.commands.config_commands import set_root

            result = set_root("111222333")

            assert result == "111222333"
            assert mock_config.root == "111222333"
            mock_config.save.assert_called_once()

    def test_set_root_interactive(self, mock_config):
        """测试交互式输入"""
        with (
            patch("ncatbot.cli.commands.config_commands.config", mock_config),
            patch("builtins.input", return_value="444555666"),
        ):
            from ncatbot.cli.commands.config_commands import set_root

            result = set_root()

            assert result == "444555666"


class TestShowConfig:
    """show_config 命令测试"""

    def test_show_config(self, mock_config, capsys):
        """测试显示配置"""
        with patch("ncatbot.cli.commands.config_commands.config", mock_config):
            from ncatbot.cli.commands.config_commands import show_config

            show_config()

            captured = capsys.readouterr()
            assert "123456789" in captured.out  # bot_uin
            assert "987654321" in captured.out  # root
            assert "ws://localhost:3001" in captured.out
