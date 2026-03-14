"""高级命令解析器高级和集成测试"""

from ncatbot.core.service.builtin.unified_registry.command_system.lexer import (
    StringTokenizer,
    AdvancedCommandParser,
    Token,
    TokenType,
)


class TestAdvancedCommandParserAdvanced:
    """高级功能测试"""

    def test_mixed_parsing(self):
        """测试混合解析"""
        parser = AdvancedCommandParser()

        # 完整的复杂命令
        command = 'backup "my files" --dest=/backup -xvf --compress=gzip document.txt --verbose'
        tokenizer = StringTokenizer(command)
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        # 检查选项
        expected_options = {"x": True, "v": True, "f": True, "verbose": True}
        assert result.options == expected_options

        # 检查命名参数
        expected_named_params = {"dest": "/backup", "compress": "gzip"}
        assert result.named_params == expected_named_params

        # 检查元素
        assert len(result.elements) == 3
        contents = [e.content for e in result.elements]
        assert contents == ["backup", "my files", "document.txt"]

        # 检查位置
        for i, element in enumerate(result.elements):
            assert element.position == i

    def test_position_preservation(self):
        """测试位置保持"""
        parser = AdvancedCommandParser()

        # 验证元素位置按原始顺序
        command = "cmd1 --opt1 arg2 -p=val arg3 --flag arg4"
        tokenizer = StringTokenizer(command)
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        # 元素应该按原始顺序
        expected_contents = ["cmd1", "arg2", "arg3", "arg4"]
        actual_contents = [e.content for e in result.elements]
        assert actual_contents == expected_contents

        # 位置应该是连续的
        for i, element in enumerate(result.elements):
            assert element.position == i

        # 选项和参数
        assert result.options == {"opt1": True, "flag": True}
        assert result.named_params == {"p": "val"}

    def test_complex_scenarios(self):
        """测试复杂场景"""
        parser = AdvancedCommandParser()

        scenarios = [
            # Docker 风格命令
            {
                "command": 'docker run --name=myapp -p=8080:80 -d "nginx:latest" --env="NODE_ENV=prod"',
                "expected_options": {"d": True},
                "expected_params": {
                    "name": "myapp",
                    "p": "8080:80",
                    "env": "NODE_ENV=prod",
                },
                "expected_elements": ["docker", "run", "nginx:latest"],
            },
            # Git 风格命令 - 简化测试，避免特殊字符问题
            {
                "command": 'git commit -m="Initial commit" --author="John Doe"',
                "expected_options": {},
                "expected_params": {"m": "Initial commit", "author": "John Doe"},
                "expected_elements": ["git", "commit"],
            },
            # 备份命令
            {
                "command": 'backup --source="/data/important" --dest="/backup" --compress --verbose',
                "expected_options": {"compress": True, "verbose": True},
                "expected_params": {"source": "/data/important", "dest": "/backup"},
                "expected_elements": ["backup"],
            },
        ]

        for scenario in scenarios:
            tokenizer = StringTokenizer(scenario["command"])
            tokens = tokenizer.tokenize()
            result = parser.parse(tokens)

            assert result.options == scenario["expected_options"], (
                f"Options failed for: {scenario['command']}"
            )
            assert result.named_params == scenario["expected_params"], (
                f"Params failed for: {scenario['command']}"
            )

            actual_contents = [e.content for e in result.elements]
            assert actual_contents == scenario["expected_elements"], (
                f"Elements failed for: {scenario['command']}"
            )

    def test_edge_cases(self):
        """测试边界情况"""
        parser = AdvancedCommandParser()

        # 空命令
        tokenizer = StringTokenizer("")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {}
        assert result.elements == []

        # 只有空白字符
        tokenizer = StringTokenizer("   ")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {}
        assert result.elements == []

        # 选项后没有值（应该被当作选项）
        tokenizer = StringTokenizer("--config=")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        # 因为没有有效的值 token，应该被当作普通选项
        assert result.options == {"config": True}
        assert result.named_params == {}

        # 只有分隔符
        tokenizer = StringTokenizer("=")
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        assert result.options == {}
        assert result.named_params == {}
        assert result.elements == []  # 分隔符被跳过

    def test_raw_tokens_preservation(self):
        """测试原始 Token 保存"""
        parser = AdvancedCommandParser()

        command = "-v --debug=true hello world"
        tokenizer = StringTokenizer(command)
        tokens = tokenizer.tokenize()
        result = parser.parse(tokens)

        # 原始 tokens 应该被保存
        assert result.raw_tokens == tokens
        assert len(result.raw_tokens) == len(tokens)

        # 验证原始 tokens 完整性
        assert any(t.type == TokenType.SHORT_OPTION for t in result.raw_tokens)
        assert any(t.type == TokenType.LONG_OPTION for t in result.raw_tokens)
        assert any(t.type == TokenType.WORD for t in result.raw_tokens)

    def test_error_resilience(self):
        """测试错误恢复能力"""
        parser = AdvancedCommandParser()

        # 处理无效的 token 序列
        # 创建一个手动构造的 token 列表
        tokens = [
            Token(TokenType.SHORT_OPTION, "v", 0),
            # 没有等号，选项当作布尔
            Token(TokenType.WORD, "hello", 2),
            Token(TokenType.EOF, "", 7),
        ]

        result = parser.parse(tokens)

        # 应该将选项当作纯选项
        assert result.options == {"v": True}
        assert result.named_params == {}
        assert len(result.elements) == 1
        assert result.elements[0].content == "hello"


def test_integration_with_string_tokenizer():
    """测试与字符串分词器的集成"""
    # 完整的集成测试
    integration_cases = [
        {
            "input": "help",
            "expected_options": {},
            "expected_params": {},
            "expected_elements": ["help"],
        },
        {
            "input": "search python --type=article -v",
            "expected_options": {"v": True},
            "expected_params": {"type": "article"},
            "expected_elements": ["search", "python"],
        },
        {
            "input": 'backup "my files" --dest="/backup" --compress',
            "expected_options": {"compress": True},
            "expected_params": {"dest": "/backup"},
            "expected_elements": ["backup", "my files"],
        },
        {
            "input": "-xvf --config=app.json process data.txt",
            "expected_options": {"x": True, "v": True, "f": True},
            "expected_params": {"config": "app.json"},
            "expected_elements": ["process", "data.txt"],
        },
    ]

    parser = AdvancedCommandParser()

    for case in integration_cases:
        # 使用 StringTokenizer 进行分词
        tokenizer = StringTokenizer(case["input"])
        tokens = tokenizer.tokenize()

        # 使用 AdvancedCommandParser 进行解析
        result = parser.parse(tokens)

        # 验证结果
        assert result.options == case["expected_options"], (
            f"Options mismatch for: {case['input']}"
        )
        assert result.named_params == case["expected_params"], (
            f"Params mismatch for: {case['input']}"
        )

        actual_elements = [e.content for e in result.elements]
        assert actual_elements == case["expected_elements"], (
            f"Elements mismatch for: {case['input']}"
        )
