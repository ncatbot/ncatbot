"""信息命令单元测试"""

from unittest.mock import MagicMock, patch


class TestShowCommandHelp:
    """show_command_help 命令测试"""

    def test_show_help_no_args(self, mock_config, capsys):
        """测试无参数显示帮助"""
        with patch("ncatbot.cli.commands.info_commands.config", mock_config):
            from ncatbot.cli.commands.info_commands import show_command_help

            show_command_help()

            captured = capsys.readouterr()
            assert "NcatBot CLI" in captured.out

    def test_show_help_for_category(self, mock_config, capsys):
        """测试显示分类帮助"""
        with patch("ncatbot.cli.commands.info_commands.config", mock_config):
            from ncatbot.cli.commands.info_commands import show_command_help

            show_command_help("sys")

            captured = capsys.readouterr()
            # 应该显示 sys 分类下的命令
            assert "start" in captured.out or "sys" in captured.out

    def test_show_help_for_command(self, mock_config, capsys):
        """测试显示特定命令帮助"""
        with patch("ncatbot.cli.commands.info_commands.config", mock_config):
            from ncatbot.cli.commands.info_commands import show_command_help

            show_command_help("start")

            captured = capsys.readouterr()
            assert "start" in captured.out
            assert "启动" in captured.out

    def test_show_help_for_alias(self, mock_config, capsys):
        """测试显示别名帮助"""
        with patch("ncatbot.cli.commands.info_commands.config", mock_config):
            from ncatbot.cli.commands.info_commands import show_command_help

            show_command_help("s")

            captured = capsys.readouterr()
            assert "别名" in captured.out

    def test_show_help_unknown_command(self, mock_config, capsys):
        """测试显示未知命令帮助"""
        with patch("ncatbot.cli.commands.info_commands.config", mock_config):
            from ncatbot.cli.commands.info_commands import show_command_help

            show_command_help("unknown_command")

            captured = capsys.readouterr()
            assert "不支持" in captured.out


class TestShowMeta:
    """show_meta 命令测试"""

    def test_show_meta(self, mock_config, capsys):
        """测试显示元信息"""
        mock_dist = MagicMock()
        mock_dist.version = "1.0.0"

        with (
            patch("ncatbot.cli.commands.info_commands.config", mock_config),
            patch("pkg_resources.get_distribution", return_value=mock_dist),
        ):
            from ncatbot.cli.commands.info_commands import show_meta

            show_meta()

            captured = capsys.readouterr()
            assert "1.0.0" in captured.out
            assert "Python" in captured.out

    def test_show_meta_error(self, mock_config, capsys):
        """测试获取版本失败"""
        with (
            patch("ncatbot.cli.commands.info_commands.config", mock_config),
            patch(
                "pkg_resources.get_distribution",
                side_effect=Exception("Not found"),
            ),
        ):
            from ncatbot.cli.commands.info_commands import show_meta

            show_meta()

            captured = capsys.readouterr()
            assert "无法获取" in captured.out


class TestShowCategories:
    """show_categories 命令测试"""

    def test_show_all_categories(self, capsys):
        """测试显示所有分类"""
        from ncatbot.cli.commands.info_commands import show_categories

        show_categories()

        captured = capsys.readouterr()
        assert "sys" in captured.out or "plg" in captured.out or "info" in captured.out

    def test_show_specific_category(self, capsys):
        """测试显示特定分类"""
        from ncatbot.cli.commands.info_commands import show_categories

        show_categories("sys")

        captured = capsys.readouterr()
        assert "start" in captured.out or "sys" in captured.out

    def test_show_unknown_category(self, capsys):
        """测试显示未知分类"""
        from ncatbot.cli.commands.info_commands import show_categories

        show_categories("unknown")

        captured = capsys.readouterr()
        assert "未知" in captured.out
