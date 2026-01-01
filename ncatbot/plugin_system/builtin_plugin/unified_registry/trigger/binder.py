"""参数绑定器（基于 message_tokenizer 结果）

策略：
- 使用 MessageTokenizer.parse_message(event.message) 获取 ParsedCommand
- 使用 FuncAnalyser 仅做签名与类型约束（detect_args_type、默认值收集）
- 位置参数绑定来源：ParsedCommand.elements（已剔除选项与命名参数）
- Sentence 类型吞剩余文本元素；MessageSegment 子类按元素匹配；基础类型从文本元素解析
"""

import inspect
from dataclasses import dataclass
from typing import Tuple, List, Any, Dict

from ..command_system.utils import (
    CommandSpec,
)
from ncatbot.utils import get_log
from ..command_system.lexer.message_tokenizer import MessageTokenizer
from ncatbot.core import MessageEvent

LOG = get_log(__name__)


class InvalidOptionError(Exception):
    def __init__(self, option_name: str):
        self.option_name = option_name
        super().__init__(f"选项 '{option_name}' 无效")


class InvalidParamError(Exception):
    def __init__(self, param_name: str):
        self.param_name = param_name
        super().__init__(f"参数 '{param_name}' 无效")


@dataclass
class BindResult:
    ok: bool
    args: Tuple  # 位置参数
    named_args: Dict[str, Any]  # 命名参数
    message: str = ""


class ArgumentBinder:
    def bind(
        self,
        spec: CommandSpec,
        event: MessageEvent,
        path_words: Tuple[str, ...],
        prefixes: List[str],
    ) -> BindResult:
        try:
            # TODO: 绑定错误回报提示
            # 解析消息为 ParsedCommand（elements 已去除选项/命名参数）
            tokenizer = MessageTokenizer()
            parsed = tokenizer.parse_message(event.message)
            elements = list(parsed.elements)  # copy
            # 跳过命令词（仅匹配前置的 text 元素）
            skip_idx = 0
            pw = list(path_words)
            pw_idx = 0
            while skip_idx < len(elements) and pw_idx < len(pw):
                el = elements[skip_idx]
                content_str = el.content
                if el.type in ("text", "plaintext") and (
                    content_str == pw[pw_idx]
                    or (len(content_str) > 0 and content_str[0] in prefixes)
                    and content_str[1:].startswith(pw[pw_idx])
                ):
                    skip_idx += 1
                    pw_idx += 1
                else:
                    break

            # 缺少参数主动抛出异常
            actual_args_count = len(elements[skip_idx:])
            sig = inspect.signature(spec.func)
            required_args = [
                name
                for name, param in sig.parameters.items()
                if param.default is inspect.Parameter.empty
                and param.kind
                in (
                    inspect.Parameter.POSITIONAL_ONLY,
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                )
            ]
            required_args_count = (
                len(required_args) - 2
            )  # 减去 self 和 cls 之类的固定参数
            if actual_args_count < required_args_count:
                raise Exception(
                    f"参数不足：需要 {required_args_count} 个，实际传入 {actual_args_count} 个"
                )

            LOG.debug(f"跳过索引: {skip_idx}")
            idx = skip_idx
            bound_args: List[Any] = []
            bound_kwargs: Dict[str, Any] = {}

            for k, v in parsed.named_params.items():
                result = spec.get_param_binding(k, v)
                if result is None:
                    raise InvalidParamError(k)
                bound_kwargs.update(result)

            for o in parsed.options:
                result = spec.get_kw_binding(o)
                if result is None:
                    raise InvalidOptionError(o)
                bound_kwargs.update(result)

            remaining_elements = elements[skip_idx:]
            args_types = spec.args_types
            
            for idx, element in enumerate(remaining_elements):
                content = element.content
                
                # 如果参数索引超出 args_types 范围，且最后一个参数是 str 类型
                # 则将剩余内容合并到最后一个参数中
                if idx >= len(args_types):
                    if args_types and args_types[-1] is str and bound_args:
                        # 将剩余元素合并到最后一个 str 参数
                        bound_args[-1] = f"{bound_args[-1]} {content}"
                    continue
                
                arg_type = args_types[idx]
                if arg_type is bool:
                    bound_args.append(content.lower() not in ["false", "0"])
                elif arg_type in (str, float, int):
                    bound_args.append(arg_type(content))
                else:
                    bound_args.append(element.content)

            return BindResult(True, tuple(bound_args), bound_kwargs, "")
        except Exception as e:
            LOG.debug(f"绑定异常: {e}")
            raise e
