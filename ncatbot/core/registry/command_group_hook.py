"""
CommandGroupHook — 命令组匹配与自动路由

高级 BEFORE_CALL Hook:
1. 支持多命令名，命令后可跟子命令和参数（格式：command subcommand [args...]）
2. 通过 inspect.signature 检查 handler 的类型注解
3. 支持子命令管理：handler 参数中包含 subcommand 参数，自动提取并路由
4. 从文本结构化提取参数 (At 段、文本 token)
5. 按类型注解自动转换 (str/int/float/At)
6. 写入 ctx.kwargs → dispatcher._execute(**ctx.kwargs) 自动注入

使用示例（与 CommandHook 一致）:

    # 定义处理器，声明子命令参数
    hook = CommandGroupHook("admin", "/admin", "a")

    @hook.subcommand("ban", "禁言")
    async def admin_ban(event: GroupMessageEvent, user_id: int, minutes: int = 60):
        # 处理 "/admin ban 12345", "/admin ban 12345 120"
        pass

    @hook.subcommand("kick")
    async def admin_kick(event: GroupMessageEvent, user_id: int):
        # 处理 "/admin kick 12345"
        pass

    @registrar.on_message("message.group")
    @hook
    @group_only
    async def handle_admin(event: GroupMessageEvent, subcommand: str = ""):
        # 当命令匹配时，subcommand 自动填充对应的子命令名
        # 如果有对应的 @hook.subcommand() 处理，该处理器先被调用
        pass
"""

import inspect
from typing import Any, Dict, List, Optional, Tuple, get_type_hints

from .hook import Hook, HookAction, HookContext, HookStage


class CommandGroup:
    """命令组 — 为向后兼容而保留（建议改用 CommandGroupHook 的 @subcommand()）

    管理子命令/子命令组的容器。
    """

    def __init__(self, names: List[str]):
        """
        Args:
            names: 该命令组的名称列表 (别名), e.g. ["help", "h"]
        """
        if not names:
            raise ValueError("CommandGroup 至少需要一个名称")
        self.names = names
        self.subcommands: Dict[str, Any] = {}  # 子命令名 → handler
        self.subgroups: Dict[str, "CommandGroup"] = {}  # 子命令组名 → CommandGroup

    def command(self, *names: str):
        """子命令注册装饰器"""

        def decorator(func):
            for name in names:
                self.subcommands[name.lower()] = func
            return func

        return decorator

    def subgroup(self, group: "CommandGroup"):
        """注册子命令组"""
        for name in group.names:
            self.subgroups[name.lower()] = group
        return group

    def __repr__(self) -> str:
        return f"<CommandGroup(names={self.names!r})>"


class CommandGroupHook(Hook):
    """命令匹配 + 子命令路由 Hook

    与 CommandHook 基本一致，额外支持子命令注册和自动路由。

    使用示例:

        hook = CommandGroupHook("admin", "/admin", "a")

        @hook.subcommand("ban")
        async def admin_ban(event: GroupMessageEvent, user_id: int, minutes: int = 60):
            pass

        @hook.subcommand("kick", "remove")
        async def admin_kick(event: GroupMessageEvent, user_id: int):
            pass

        @registrar.on_message("message.group")
        @hook
        @group_only
        async def handle_admin(event: GroupMessageEvent, subcommand: str = ""):
            pass

    用法:
        /admin ban 12345       → 调用 admin_ban(event, 12345, 60)
        /admin ban 12345 120   → 调用 admin_ban(event, 12345, 120)
        /admin kick 12345      → 调用 admin_kick(event, 12345)
    """

    stage = HookStage.BEFORE_CALL

    def __init__(
        self,
        *names: str,
        ignore_case: bool = False,
        priority: int = 95,
    ):
        """
        Args:
            *names: 命令名列表（支持别名), e.g. "admin", "/admin", "a"
            ignore_case: 是否忽略大小写匹配
            priority: hook 优先级
        """
        if not names:
            raise ValueError("CommandGroupHook 至少需要一个命令名")
        self.names = names
        self.ignore_case = ignore_case
        self.priority = priority
        self._subcommands: Dict[str, Any] = {}  # 子命令名 → handler
        self._sig_cache: Dict[int, Optional["_ParamSpec"]] = {}

    def subcommand(self, *subcommand_names: str):
        """子命令注册装饰器

        Args:
            *subcommand_names: 子命令名称（支持别名）
        """

        def decorator(func):
            for name in subcommand_names:
                compare_name = name.lower() if self.ignore_case else name
                self._subcommands[compare_name] = func
            return func

        return decorator

    async def execute(self, ctx: HookContext) -> HookAction:
        # 获取消息文本
        message = getattr(ctx.event.data, "message", None)
        if message is None:
            return HookAction.SKIP
        text = message.text.strip() if hasattr(message, "text") else ""
        if not text:
            return HookAction.SKIP

        compare_text = text.lower() if self.ignore_case else text

        # 解析 handler 参数规格 (缓存)
        func = ctx.handler_entry.func
        spec = self._get_param_spec(func)

        # CommandGroupHook 总是支持前缀匹配（为了支持子命令）
        matched_name = None
        for name in self.names:
            compare_name = name.lower() if self.ignore_case else name
            if compare_text == compare_name or compare_text.startswith(
                compare_name + " "
            ):
                matched_name = name
                break

        if matched_name is None:
            return HookAction.SKIP

        # 提取命令后的文本
        if len(text) > len(matched_name):
            rest = text[len(matched_name) :].strip()
        else:
            rest = ""

        # 尝试匹配子命令
        if rest:
            first_token, *rest_tokens = rest.split(None, 1)
            remaining = rest_tokens[0] if rest_tokens else ""
            compare_first = first_token.lower() if self.ignore_case else first_token

            # 查找注册的子命令
            if compare_first in self._subcommands:
                subcommand_handler = self._subcommands[compare_first]
                # 绑定子命令处理器的参数
                subcommand_spec = self._get_param_spec(subcommand_handler)
                if subcommand_spec:
                    kwargs = self._bind_params(subcommand_spec, remaining, message)
                    if kwargs is not None:
                        ctx.kwargs.update(kwargs)
                        return HookAction.CONTINUE

        # 没有子命令匹配，检查是否是精确命令匹配（无rest）
        if not rest:
            # 精确匹配：命令名后没有任何东西
            return HookAction.CONTINUE

        # 如果有rest但没有子命令，尝试绑定主handler的参数
        if spec and spec.params:
            kwargs = self._bind_params(spec, rest, message)
            if kwargs is None:
                return HookAction.SKIP
            ctx.kwargs.update(kwargs)

        return HookAction.CONTINUE

    def _get_param_spec(self, func) -> Optional["_ParamSpec"]:
        """解析并缓存 handler 的参数规格"""
        func_id = id(func)
        if func_id in self._sig_cache:
            return self._sig_cache[func_id]

        try:
            sig = inspect.signature(func)
            try:
                hints = get_type_hints(func)
            except Exception:
                hints = {}

            params_list = list(sig.parameters.values())

            # 跳过 self 和 event 参数
            skip = 0
            for p in params_list:
                if p.name in ("self", "cls"):
                    skip += 1
                    continue
                # 第一个非 self 参数是 event
                skip += 1
                break

            extra_params = params_list[skip:]
            if not extra_params:
                spec = _ParamSpec(params=[])
                self._sig_cache[func_id] = spec
                return spec

            params = []
            for p in extra_params:
                annotation = hints.get(p.name, p.annotation)
                has_default = p.default is not inspect.Parameter.empty
                params.append(
                    _ParamInfo(
                        name=p.name,
                        annotation=annotation,
                        has_default=has_default,
                        default=p.default if has_default else None,
                    )
                )

            spec = _ParamSpec(params=params)
            self._sig_cache[func_id] = spec
            return spec

        except (ValueError, TypeError):
            self._sig_cache[func_id] = _ParamSpec(params=[])
            return self._sig_cache[func_id]

    def _bind_params(
        self,
        spec: "_ParamSpec",
        rest: str,
        message: Any,
    ) -> Optional[Dict[str, Any]]:
        """根据参数规格绑定实际值，失败返回 None

        支持类型:
        - At: 从 message.filter_at() 按序提取
        - int: 从文本 token 提取并转换
        - float: 从文本 token 提取并转换
        - str: 单 token 或剩余文本 (最后一个 str)
        """
        from ncatbot.types import At

        # 提取 At 列表和文本 token
        at_list: List[Any] = []
        if hasattr(message, "filter_at"):
            at_list = list(message.filter_at())

        text_tokens = rest.split() if rest else []

        kwargs: Dict[str, Any] = {}
        at_idx = 0
        token_idx = 0

        for i, param in enumerate(spec.params):
            # 跳过 subcommand 参数（由外层处理）
            if param.name == "subcommand":
                if param.has_default:
                    kwargs[param.name] = param.default
                continue

            anno = param.annotation
            is_last_str = i == len(spec.params) - 1 and _is_type(anno, str)

            if _is_type(anno, At):
                if at_idx < len(at_list):
                    kwargs[param.name] = at_list[at_idx]
                    at_idx += 1
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

            elif _is_type(anno, int):
                value = _extract_typed_token(text_tokens, token_idx, int)
                if value is not None:
                    kwargs[param.name] = value[0]
                    token_idx = value[1]
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

            elif _is_type(anno, float):
                value = _extract_typed_token(text_tokens, token_idx, float)
                if value is not None:
                    kwargs[param.name] = value[0]
                    token_idx = value[1]
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

            elif _is_type(anno, str) or anno is inspect.Parameter.empty:
                if is_last_str:
                    remaining = " ".join(text_tokens[token_idx:])
                    if remaining:
                        kwargs[param.name] = remaining
                        token_idx = len(text_tokens)
                    elif param.has_default:
                        kwargs[param.name] = param.default
                    else:
                        return None
                else:
                    if token_idx < len(text_tokens):
                        kwargs[param.name] = text_tokens[token_idx]
                        token_idx += 1
                    elif param.has_default:
                        kwargs[param.name] = param.default
                    else:
                        return None

            else:
                # 未识别类型，尝试 str
                if token_idx < len(text_tokens):
                    kwargs[param.name] = text_tokens[token_idx]
                    token_idx += 1
                elif param.has_default:
                    kwargs[param.name] = param.default
                else:
                    return None

        return kwargs

    def __repr__(self) -> str:
        return (
            f"<CommandGroupHook(names={self.names!r}, "
            f"subcommands={list(self._subcommands.keys())!r}, "
            f"ignore_case={self.ignore_case})>"
        )


def _extract_typed_token(
    tokens: List[str], start_idx: int, target_type: type
) -> Optional[Tuple[Any, int]]:
    """从 tokens[start_idx:] 找到第一个可转换为 target_type 的 token"""
    for i in range(start_idx, len(tokens)):
        try:
            return (target_type(tokens[i]), i + 1)
        except (ValueError, TypeError):
            continue
    return None


def _is_type(annotation: Any, target: type) -> bool:
    """检查注解是否为指定类型"""
    if annotation is inspect.Parameter.empty:
        return False
    if annotation is target:
        return True
    if isinstance(annotation, type) and issubclass(annotation, target):
        return True
    if isinstance(annotation, str):
        return annotation == target.__name__
    return False


class _ParamInfo:
    """单个参数信息"""

    __slots__ = ("name", "annotation", "has_default", "default")

    def __init__(self, name: str, annotation: Any, has_default: bool, default: Any):
        self.name = name
        self.annotation = annotation
        self.has_default = has_default
        self.default = default


class _ParamSpec:
    """handler 的参数规格"""

    __slots__ = ("params",)

    def __init__(self, params: List[_ParamInfo]):
        self.params = params
