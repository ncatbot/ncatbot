"""消息级别分词器测试

测试 MessageTokenizer 和相关功能，包括：
- MessageArray 到 Token 序列的转换
- 文本和非文本元素的混合处理
- 组合参数支持 (--para=[图片])
- 完整的消息级别命令解析
"""

from ncatbot.core.service.builtin.unified_registry.command_system.lexer import (
    MessageTokenizer,
    parse_message_command,
    TokenType,
    NonTextToken,
)
from ncatbot.core.event.message_segments import MessageArray, PlainText, At, Image


class TestMessageTokenizer:
    """消息级别分词器测试类"""

    def test_text_only_message(self):
        """测试纯文本消息"""
        message_array = MessageArray(
            PlainText(text="backup"),
            PlainText(text="--dest=/backup"),
            PlainText(text="-v"),
            PlainText(text='"my files"'),
        )

        tokenizer = MessageTokenizer()
        tokens = tokenizer.tokenize(message_array)

        # 验证 token 类型和数量
        text_tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(text_tokens) == 6  # backup, --dest, =, /backup, -v, "my files"

        # 验证具体内容
        assert text_tokens[0].type == TokenType.WORD
        assert text_tokens[0].value == "backup"
        assert text_tokens[1].type == TokenType.LONG_OPTION
        assert text_tokens[1].value == "dest"
        assert text_tokens[2].type == TokenType.SEPARATOR
        assert text_tokens[5].type == TokenType.QUOTED_STRING
        assert text_tokens[5].value == "my files"

    def test_mixed_message(self):
        """测试混合消息（文本 + 非文本）"""
        message_array = MessageArray(
            PlainText(text="backup"),
            At(qq="123456"),
            PlainText(text="--dest=/backup"),
            Image(file="preview.jpg"),
            PlainText(text="-v"),
        )

        tokenizer = MessageTokenizer()
        tokens = tokenizer.tokenize(message_array)

        # 验证混合 token 序列
        non_eof_tokens = [t for t in tokens if t.type != TokenType.EOF]
        assert len(non_eof_tokens) == 7  # backup, [at], --dest, =, /backup, [image], -v

        # 验证 NonTextToken
        at_token = non_eof_tokens[1]
        assert isinstance(at_token, NonTextToken)
        assert at_token.type == TokenType.NON_TEXT_ELEMENT
        assert at_token.element_type == "at"
        assert at_token.value == "[at]"
        assert at_token.segment.qq == "123456"

        image_token = non_eof_tokens[5]
        assert isinstance(image_token, NonTextToken)
        assert image_token.element_type == "image"
        assert image_token.segment.file == "preview.jpg"

    def test_combined_parameters(self):
        """测试组合参数 --para=[图片]"""
        message_array = MessageArray(
            PlainText(text="deploy"),
            PlainText(text="--preview="),
            Image(file="app_screenshot.png"),
            PlainText(text="--config=/etc/app.conf"),
            PlainText(text="-v"),
        )

        tokenizer = MessageTokenizer()
        result = tokenizer.parse_message(message_array)

        # 验证解析结果
        assert result.options == {"v": True}

        # 验证命名参数
        assert len(result.named_params) == 2
        assert result.named_params["config"] == "/etc/app.conf"

        # 验证非文本参数
        preview_param = result.named_params.get("preview")
        assert preview_param is not None
        assert hasattr(preview_param, "file")
        assert preview_param.file == "app_screenshot.png"

        # 验证元素
        assert len(result.elements) == 1
        assert result.elements[0].content == "deploy"

    def test_multiple_nontext_elements(self):
        """测试多个非文本元素"""
        message_array = MessageArray(
            PlainText(text="notify"),
            At(qq="111111"),
            At(qq="222222"),
            PlainText(text="--attachment="),
            Image(file="document.pdf"),
            PlainText(text="--urgent"),
        )

        tokenizer = MessageTokenizer()
        result = tokenizer.parse_message(message_array)

        # 验证选项
        assert result.options == {"urgent": True}

        # 验证非文本参数
        attachment = result.named_params.get("attachment")
        assert attachment is not None
        assert attachment.file == "document.pdf"

        # 验证多个 @ 元素
        at_elements = [e for e in result.elements if e.type == "at"]
        assert len(at_elements) == 2
        assert at_elements[0].content.qq == "111111"
        assert at_elements[1].content.qq == "222222"

    def test_complex_mixed_command(self):
        """测试复杂的混合命令"""
        message_array = MessageArray(
            [
                PlainText(text="process"),
                PlainText(text='"input file.txt"'),
                PlainText(text="--output="),
                Image(file="result.png"),
                At(qq="123456"),
                PlainText(text="--format=json"),
                PlainText(text="-xvf"),
                PlainText(text="--notify"),
            ]
        )

        tokenizer = MessageTokenizer()
        result = tokenizer.parse_message(message_array)

        # 验证选项
        expected_options = {"x": True, "v": True, "f": True, "notify": True}
        assert result.options == expected_options

        # 验证命名参数
        assert result.named_params["format"] == "json"
        assert hasattr(result.named_params["output"], "file")
        assert result.named_params["output"].file == "result.png"

        # 验证元素
        text_elements = [e for e in result.elements if e.type == "text"]
        at_elements = [e for e in result.elements if e.type == "at"]

        assert len(text_elements) == 2  # "process", "input file.txt"
        assert len(at_elements) == 1  # @admin

        assert text_elements[0].content == "process"
        assert text_elements[1].content == "input file.txt"
        assert at_elements[0].content.qq == "123456"

    def test_edge_cases(self):
        """测试边界情况"""
        # 空消息
        empty_message = MessageArray([])
        tokenizer = MessageTokenizer()
        result = tokenizer.parse_message(empty_message)

        assert result.options == {}
        assert result.named_params == {}
        assert result.elements == []

        # 只有非文本元素
        nontext_only = MessageArray([At(qq="123"), Image(file="pic.jpg")])

        result = tokenizer.parse_message(nontext_only)
        assert len(result.elements) == 2
        assert all(e.type in ["at", "image"] for e in result.elements)

        # 只有选项，无普通元素
        options_only = MessageArray(
            [
                PlainText(text="-xvf"),
                PlainText(text="--debug"),
                PlainText(text="--config=app.json"),
            ]
        )

        result = tokenizer.parse_message(options_only)
        assert result.options == {"x": True, "v": True, "f": True, "debug": True}
        assert result.named_params == {"config": "app.json"}
        assert result.elements == []

    def test_position_tracking(self):
        """测试位置跟踪"""
        message_array = MessageArray(
            [
                PlainText(text="cmd"),
                At(qq="123"),
                PlainText(text="arg1"),
                Image(file="img.jpg"),
                PlainText(text="arg2"),
            ]
        )

        tokenizer = MessageTokenizer()
        tokens = tokenizer.tokenize(message_array)

        # 验证位置递增
        positions = [t.position for t in tokens if t.type != TokenType.EOF]
        assert positions == list(range(len(positions)))

        # 验证解析后的元素位置
        result = tokenizer.parse_message(message_array)
        element_positions = [e.position for e in result.elements]
        assert element_positions == list(range(len(result.elements)))

    def test_utility_methods(self):
        """测试工具方法"""
        message_array = MessageArray(
            [
                PlainText(text="test"),
                PlainText(text="--text=value"),
                PlainText(text="--image="),
                Image(file="test.jpg"),
                PlainText(text="--flag"),
            ]
        )

        result = parse_message_command(message_array)

        # 测试分离方法
        text_params = result.get_text_params()
        segment_params = result.get_segment_params()

        assert text_params == {"text": "value"}
        assert len(segment_params) == 1
        assert "image" in segment_params
        assert segment_params["image"].file == "test.jpg"


def test_convenience_function():
    """测试便捷函数"""
    message_array = MessageArray(
        [PlainText(text="hello"), PlainText(text="--name=world"), At(qq="123456")]
    )

    # 使用便捷函数
    result = parse_message_command(message_array)

    assert result.named_params["name"] == "world"
    assert len(result.elements) == 2  # "hello" 和 @123456
    assert result.elements[0].content == "hello"
    assert result.elements[1].type == "at"


if __name__ == "__main__":
    print("运行消息级别分词器测试...")

    # 创建测试实例
    test_instance = TestMessageTokenizer()

    # 运行所有测试方法
    test_methods = [
        ("纯文本消息", test_instance.test_text_only_message),
        ("混合消息", test_instance.test_mixed_message),
        ("组合参数", test_instance.test_combined_parameters),
        ("多个非文本元素", test_instance.test_multiple_nontext_elements),
        ("复杂混合命令", test_instance.test_complex_mixed_command),
        ("边界情况", test_instance.test_edge_cases),
        ("位置跟踪", test_instance.test_position_tracking),
        ("工具方法", test_instance.test_utility_methods),
    ]

    for test_name, test_method in test_methods:
        try:
            test_method()
            print(f"✓ {test_name}测试通过")
        except Exception as e:
            print(f"✗ {test_name}测试失败: {e}")
            raise

    # 便捷函数测试
    try:
        test_convenience_function()
        print("✓ 便捷函数测试通过")
    except Exception as e:
        print(f"✗ 便捷函数测试失败: {e}")
        raise

    print("\n消息级别分词器所有测试通过！✨")

    # 演示用法
    print("\n=== 用法演示 ===")
    demo_message = MessageArray(
        [
            PlainText(text="backup"),
            PlainText(text='"important files"'),
            PlainText(text="--preview="),
            Image(file="preview.jpg"),
            At(qq="admin"),
            PlainText(text="--dest=/backup"),
            PlainText(text="-xvf"),
        ]
    )

    result = parse_message_command(demo_message)

    print(f"选项: {result.options}")
    print(f"文本参数: {result.get_text_params()}")
    print(f"非文本参数: {list(result.get_segment_params().keys())}")
    element_info = []
    for e in result.elements:
        if e.type == "text":
            element_info.append((e.type, e.content))
        else:
            detail = getattr(e.content, "qq", getattr(e.content, "file", "unknown"))
            element_info.append((e.type, f"{e.type}:{detail}"))
    print(f"元素: {element_info}")

    print("\n消息级别命令解析完成！支持文本和非文本元素的混合处理 🎉")
