"""命令注册表单元测试"""

from ncatbot.cli.commands.registry import Command, CommandRegistry


class TestCommand:
    """Command 类测试"""

    def test_command_init_basic(self):
        """测试基本的命令初始化"""

        def dummy_func():
            pass

        cmd = Command(
            name="test",
            func=dummy_func,
            description="测试命令",
            usage="test",
        )

        assert cmd.name == "test"
        assert cmd.func == dummy_func
        assert cmd.description == "测试命令"
        assert cmd.usage == "test"
        assert cmd.help_text == "测试命令"  # 默认与 description 相同
        assert cmd.aliases == []
        assert cmd.category == "General"
        assert cmd.show_in_help is True

    def test_command_init_with_options(self):
        """测试带选项的命令初始化"""

        def dummy_func():
            pass

        cmd = Command(
            name="test",
            func=dummy_func,
            description="测试命令",
            usage="test <arg>",
            help_text="详细帮助",
            aliases=["t", "tst"],
            category="sys",
            show_in_help=False,
        )

        assert cmd.help_text == "详细帮助"
        assert cmd.aliases == ["t", "tst"]
        assert cmd.category == "sys"
        assert cmd.show_in_help is False


class TestCommandRegistry:
    """CommandRegistry 类测试"""

    def test_registry_init(self):
        """测试注册表初始化"""
        registry = CommandRegistry()

        assert registry.commands == {}
        assert registry.aliases == {}
        assert registry.categories == {}

    def test_register_command(self):
        """测试命令注册"""
        registry = CommandRegistry()

        @registry.register(
            name="hello",
            description="打招呼",
            usage="hello",
            category="test",
        )
        def hello():
            return "Hello!"

        assert "hello" in registry.commands
        assert registry.commands["hello"].name == "hello"
        assert registry.commands["hello"].description == "打招呼"
        assert "test" in registry.categories
        assert "hello" in registry.categories["test"]

    def test_register_command_with_aliases(self):
        """测试带别名的命令注册"""
        registry = CommandRegistry()

        @registry.register(
            name="start",
            description="启动",
            usage="start",
            aliases=["s", "run"],
            category="sys",
        )
        def start():
            pass

        assert "s" in registry.aliases
        assert "run" in registry.aliases
        assert registry.aliases["s"] == "start"
        assert registry.aliases["run"] == "start"

    def test_execute_command(self):
        """测试命令执行"""
        registry = CommandRegistry()

        @registry.register(
            name="add",
            description="加法",
            usage="add <a> <b>",
        )
        def add(a, b):
            return int(a) + int(b)

        result = registry.execute("add", "2", "3")
        assert result == 5

    def test_execute_command_via_alias(self):
        """测试通过别名执行命令"""
        registry = CommandRegistry()

        @registry.register(
            name="greet",
            description="问候",
            usage="greet <name>",
            aliases=["g"],
        )
        def greet(name):
            return f"Hello, {name}!"

        result = registry.execute("g", "World")
        assert result == "Hello, World!"

    def test_execute_unknown_command(self, capsys):
        """测试执行未知命令"""
        registry = CommandRegistry()

        result = registry.execute("unknown")

        assert result is None
        captured = capsys.readouterr()
        assert "不支持的命令" in captured.out

    def test_get_categories(self):
        """测试获取分类列表"""
        registry = CommandRegistry()

        @registry.register(name="cmd1", description="", usage="", category="sys")
        def cmd1():
            pass

        @registry.register(name="cmd2", description="", usage="", category="plg")
        def cmd2():
            pass

        @registry.register(name="cmd3", description="", usage="", category="info")
        def cmd3():
            pass

        categories = registry.get_categories()
        assert sorted(categories) == ["info", "plg", "sys"]

    def test_get_commands_by_category(self):
        """测试按分类获取命令"""
        registry = CommandRegistry()

        @registry.register(name="start", description="启动", usage="", category="sys")
        def start():
            pass

        @registry.register(name="stop", description="停止", usage="", category="sys")
        def stop():
            pass

        @registry.register(name="help", description="帮助", usage="", category="info")
        def help_cmd():
            pass

        sys_commands = registry.get_commands_by_category("sys")
        assert len(sys_commands) == 2
        assert any(name == "start" for name, _ in sys_commands)
        assert any(name == "stop" for name, _ in sys_commands)

    def test_get_help(self):
        """测试获取帮助信息"""
        registry = CommandRegistry()

        @registry.register(
            name="test",
            description="测试命令",
            usage="test",
            aliases=["t"],
        )
        def test_cmd():
            pass

        help_text = registry.get_help()
        assert "test" in help_text
        assert "测试命令" in help_text

    def test_get_help_by_category(self):
        """测试按分类获取帮助"""
        registry = CommandRegistry()

        @registry.register(
            name="cmd1", description="命令1", usage="cmd1", category="sys"
        )
        def cmd1():
            pass

        @registry.register(
            name="cmd2", description="命令2", usage="cmd2", category="plg"
        )
        def cmd2():
            pass

        help_text = registry.get_help("sys")
        assert "命令1" in help_text
        assert "命令2" not in help_text

    def test_get_help_unknown_category(self):
        """测试获取未知分类的帮助"""
        registry = CommandRegistry()

        help_text = registry.get_help("unknown")
        assert "未知的分类" in help_text
