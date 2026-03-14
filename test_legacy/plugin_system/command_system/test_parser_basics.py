"""高级命令解析器基础测试"""

from ncatbot.core.service.builtin.unified_registry.command_system.lexer import (
    StringTokenizer,
    AdvancedCommandParser,
)


class TestAdvancedCommandParserBasics:
    """基础功能测试"""

    def test_options_parsing(self):
        """测试选项解析"""
        parser = AdvancedCommandParser()

        # 短选项
        tokenizer = StringTokenizer("-v")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {"v": True}
        assert result.named_params == {}
        assert result.elements == []

        # 组合短选项
        tokenizer = StringTokenizer("-xvf")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {"x": True, "v": True, "f": True}
        assert result.named_params == {}
        assert result.elements == []

        # 长选项
        tokenizer = StringTokenizer("--verbose --debug")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {"verbose": True, "debug": True}
        assert result.named_params == {}
        assert result.elements == []

        # 混合选项
        tokenizer = StringTokenizer("-v --debug -xf --help")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        expected_options = {
            "v": True,
            "debug": True,
            "x": True,
            "f": True,
            "help": True,
        }
        assert result.options == expected_options
        assert result.named_params == {}
        assert result.elements == []

    def test_named_params_parsing(self):
        """测试命名参数解析"""
        parser = AdvancedCommandParser()

        # 短选项赋值
        tokenizer = StringTokenizer("-p=8080")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {"p": "8080"}
        assert result.elements == []

        # 长选项赋值
        tokenizer = StringTokenizer("--port=8080 --host=localhost")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {"port": "8080", "host": "localhost"}
        assert result.elements == []

        # 引用字符串赋值
        tokenizer = StringTokenizer('--message="hello world" -c="gzip"')
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {"message": "hello world", "c": "gzip"}
        assert result.elements == []

        # 复杂值
        tokenizer = StringTokenizer(
            '--env="NODE_ENV=production" --config="/path/to/config.json"'
        )
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        expected_params = {
            "env": "NODE_ENV=production",
            "config": "/path/to/config.json",
        }
        assert result.named_params == expected_params

    def test_elements_parsing(self):
        """测试 Element 解析"""
        parser = AdvancedCommandParser()

        # 基本元素
        tokenizer = StringTokenizer('backup "my files" document.txt')
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {}
        assert len(result.elements) == 3

        # 检查元素内容和位置
        assert result.elements[0].type == "text"
        assert result.elements[0].content == "backup"
        assert result.elements[0].position == 0

        assert result.elements[1].type == "text"
        assert result.elements[1].content == "my files"
        assert result.elements[1].position == 1

        assert result.elements[2].type == "text"
        assert result.elements[2].content == "document.txt"
        assert result.elements[2].position == 2

        # 只有引用字符串
        tokenizer = StringTokenizer('"first string" "second string"')
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert len(result.elements) == 2
        assert result.elements[0].content == "first string"
        assert result.elements[1].content == "second string"

        # 混合元素类型
        tokenizer = StringTokenizer('command "quoted arg" normal_arg')
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert len(result.elements) == 3
        contents = [e.content for e in result.elements]
        assert contents == ["command", "quoted arg", "normal_arg"]
