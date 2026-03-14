"""CLI 命令端到端测试

不使用任何 mock，测试真实的 CLI 命令执行流程。
"""

import io
import sys
from contextlib import redirect_stdout


from ncatbot.cli.commands.registry import registry


class TestHelpCommand:
    """help 命令端到端测试"""

    def test_help_shows_all_categories(self):
        """测试 help 显示所有分类"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("help")

        result = output.getvalue()
        # 验证输出包含预期内容
        assert "NcatBot" in result
        assert len(result) > 100  # 应该有足够的内容

    def test_help_for_specific_command(self):
        """测试查看特定命令帮助"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("help", "start")

        result = output.getvalue()
        assert "start" in result
        assert "启动" in result

    def test_help_for_category(self):
        """测试查看分类帮助"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("help", "sys")

        result = output.getvalue()
        # 应该列出 sys 分类下的命令
        assert "sys" in result.lower() or "start" in result


class TestCategoriesCommand:
    """categories 命令端到端测试"""

    def test_categories_lists_all(self):
        """测试列出所有分类"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("categories")

        result = output.getvalue()
        assert "sys" in result
        assert "plg" in result
        assert "info" in result

    def test_categories_filter_by_name(self):
        """测试按名称筛选分类"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("categories", "sys")

        result = output.getvalue()
        assert "start" in result or "setqq" in result


class TestMetaCommand:
    """meta 命令端到端测试"""

    def test_meta_shows_version(self):
        """测试显示版本信息"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("meta")

        result = output.getvalue()
        # 应该包含版本相关信息
        assert "Python" in result or "版本" in result


class TestPluginCreateCommand:
    """create 命令端到端测试"""

    def test_create_plugin_template(self, cli_test_env):
        """测试创建插件模板"""
        plugins_dir = cli_test_env["plugins_dir"]

        output = io.StringIO()
        stdin_backup = sys.stdin
        sys.stdin = io.StringIO("TestAuthor\n")

        try:
            with redirect_stdout(output):
                registry.execute("create", "e2e_test_plugin")
        finally:
            sys.stdin = stdin_backup

        result = output.getvalue()
        assert "创建成功" in result

        # 验证文件实际创建
        plugin_dir = plugins_dir / "e2e_test_plugin"
        assert plugin_dir.exists()
        assert (plugin_dir / "manifest.toml").exists()
        assert (plugin_dir / "plugin.py").exists()
        assert (plugin_dir / "__init__.py").exists()

        # 验证 manifest 内容
        manifest_content = (plugin_dir / "manifest.toml").read_text(encoding="utf-8")
        assert 'name = "e2e_test_plugin"' in manifest_content
        assert 'author = "TestAuthor"' in manifest_content

    def test_create_plugin_invalid_name(self, cli_test_env):
        """测试创建无效名称的插件"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("create", "123invalid")

        result = output.getvalue()
        assert "不合法" in result

    def test_create_plugin_with_underscore(self, cli_test_env):
        """测试创建带下划线的插件名"""
        plugins_dir = cli_test_env["plugins_dir"]

        stdin_backup = sys.stdin
        sys.stdin = io.StringIO("Author\n")

        try:
            output = io.StringIO()
            with redirect_stdout(output):
                registry.execute("create", "my_cool_plugin")
        finally:
            sys.stdin = stdin_backup

        assert (plugins_dir / "my_cool_plugin").exists()


class TestPluginListCommand:
    """list 命令端到端测试"""

    def test_list_empty_plugins_dir(self, cli_test_env):
        """测试列出空的插件目录"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("list")

        result = output.getvalue()
        assert "没有安装" in result

    def test_list_with_plugins(self, sample_plugin_in_env, cli_test_env):
        """测试列出已安装的插件"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("list")

        result = output.getvalue()
        assert "sample_plugin" in result
        assert "1.0.0" in result
        assert "Test Author" in result


class TestPluginRemoveCommand:
    """remove 命令端到端测试"""

    def test_remove_existing_plugin(self, sample_plugin_in_env, cli_test_env):
        """测试删除已存在的插件"""
        plugin_dir = sample_plugin_in_env
        assert plugin_dir.exists()

        stdin_backup = sys.stdin
        sys.stdin = io.StringIO("y\n")

        try:
            output = io.StringIO()
            with redirect_stdout(output):
                registry.execute("remove", "sample_plugin")
        finally:
            sys.stdin = stdin_backup

        result = output.getvalue()
        assert "已删除" in result
        assert not plugin_dir.exists()

    def test_remove_nonexistent_plugin(self, cli_test_env):
        """测试删除不存在的插件"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("remove", "nonexistent_plugin")

        result = output.getvalue()
        assert "不存在" in result

    def test_remove_cancel(self, sample_plugin_in_env, cli_test_env):
        """测试取消删除"""
        plugin_dir = sample_plugin_in_env

        stdin_backup = sys.stdin
        sys.stdin = io.StringIO("n\n")

        try:
            output = io.StringIO()
            with redirect_stdout(output):
                registry.execute("remove", "sample_plugin")
        finally:
            sys.stdin = stdin_backup

        result = output.getvalue()
        assert "已取消" in result
        assert plugin_dir.exists()


class TestConfigCommand:
    """config 命令端到端测试"""

    def test_config_shows_current_settings(self, cli_test_env):
        """测试显示当前配置"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("config")

        result = output.getvalue()
        assert "机器人 QQ" in result or "QQ" in result
        assert "插件目录" in result


class TestAliasResolution:
    """别名解析端到端测试"""

    def test_alias_h_resolves_to_help(self):
        """测试 h 别名解析为 help"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("h")

        result = output.getvalue()
        assert "NcatBot" in result

    def test_alias_ls_resolves_to_list(self, cli_test_env):
        """测试 ls 别名解析为 list"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("ls")

        result = output.getvalue()
        assert "没有安装" in result or "已安装" in result

    def test_alias_cat_resolves_to_categories(self):
        """测试 cat 别名解析为 categories"""
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("cat")

        result = output.getvalue()
        assert "分类" in result or "sys" in result


class TestCommandWorkflow:
    """命令工作流端到端测试"""

    def test_create_list_remove_workflow(self, cli_test_env):
        """测试创建 -> 列出 -> 删除的完整工作流"""
        plugins_dir = cli_test_env["plugins_dir"]

        # Step 1: 创建插件
        stdin_backup = sys.stdin
        sys.stdin = io.StringIO("WorkflowAuthor\n")
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                registry.execute("create", "workflow_plugin")
        finally:
            sys.stdin = stdin_backup

        assert "创建成功" in output.getvalue()
        plugin_dir = plugins_dir / "workflow_plugin"
        assert plugin_dir.exists()

        # Step 2: 列出插件
        output = io.StringIO()
        with redirect_stdout(output):
            registry.execute("list")

        assert "workflow_plugin" in output.getvalue()

        # Step 3: 删除插件
        sys.stdin = io.StringIO("y\n")
        try:
            output = io.StringIO()
            with redirect_stdout(output):
                registry.execute("remove", "workflow_plugin")
        finally:
            sys.stdin = stdin_backup

        assert "已删除" in output.getvalue()
        assert not plugin_dir.exists()


class TestCommandRegistration:
    """命令注册完整性测试"""

    def test_all_expected_commands_registered(self):
        """测试所有预期命令都已注册"""
        expected_commands = [
            "start",
            "update",
            "exit",
            "setqq",
            "setroot",
            "config",
            "create",
            "remove",
            "list",
            "help",
            "meta",
            "categories",
        ]

        for cmd in expected_commands:
            assert cmd in registry.commands, f"命令 '{cmd}' 应该已注册"

    def test_all_expected_aliases_registered(self):
        """测试所有预期别名都已注册"""
        expected_aliases = {
            "s": "start",
            "run": "start",
            "u": "update",
            "q": "exit",
            "qq": "setqq",
            "new": "create",
            "rm": "remove",
            "ls": "list",
            "h": "help",
            "?": "help",
            "v": "meta",
            "cat": "categories",
        }

        for alias, target in expected_aliases.items():
            assert alias in registry.aliases, f"别名 '{alias}' 应该已注册"
            assert registry.aliases[alias] == target, (
                f"别名 '{alias}' 应该指向 '{target}'"
            )

    def test_all_categories_have_commands(self):
        """测试所有分类都有命令"""
        categories = registry.get_categories()

        for category in categories:
            commands = registry.get_commands_by_category(category)
            assert len(commands) > 0, f"分类 '{category}' 应该有命令"

    def test_all_commands_visible_in_help(self):
        """测试所有命令都在帮助中可见"""
        for name, cmd in registry.commands.items():
            assert cmd.show_in_help is True, f"命令 '{name}' 应该在帮助中可见"
