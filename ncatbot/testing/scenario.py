"""
Scenario — 链式测试场景构建器

以声明式 API 描述测试流程，然后一次性执行并断言::

    await (
        Scenario("群消息回复")
        .inject(group_message("hello"))
        .settle()
        .assert_api_called("post_group_msg")
        .run(harness)
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from ncatbot.testing.harness import TestHarness
    from ncatbot.types import BaseEventData


class _StepKind(Enum):
    INJECT = auto()
    SETTLE = auto()
    ASSERT_API_CALLED = auto()
    ASSERT_API_NOT_CALLED = auto()
    ASSERT_API_COUNT = auto()
    ASSERT_CUSTOM = auto()
    RESET_API = auto()


@dataclass
class _Step:
    kind: _StepKind
    kwargs: Dict[str, Any] = field(default_factory=dict)


class Scenario:
    """链式测试场景构建器。

    所有链式方法返回 self 以支持流式调用。
    调用 ``await scenario.run(harness)`` 执行全部步骤。
    """

    def __init__(self, name: str = "") -> None:
        self._name = name
        self._steps: List[_Step] = []

    # ---- 事件注入 ----

    def inject(self, event_data: "BaseEventData") -> "Scenario":
        """注入一个事件"""
        self._steps.append(_Step(kind=_StepKind.INJECT, kwargs={"event": event_data}))
        return self

    def inject_many(self, events: List["BaseEventData"]) -> "Scenario":
        """注入多个事件"""
        for ev in events:
            self.inject(ev)
        return self

    # ---- 同步/等待 ----

    def settle(self, delay: float = 0.05) -> "Scenario":
        """等待 handler 处理完成"""
        self._steps.append(_Step(kind=_StepKind.SETTLE, kwargs={"delay": delay}))
        return self

    # ---- 断言 ----

    def assert_api_called(self, action: str, **match: Any) -> "Scenario":
        """断言某 API 被调用（可选检查参数匹配）"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_CALLED,
                kwargs={"action": action, "match": match},
            )
        )
        return self

    def assert_api_not_called(self, action: str) -> "Scenario":
        """断言某 API 未被调用"""
        self._steps.append(
            _Step(kind=_StepKind.ASSERT_API_NOT_CALLED, kwargs={"action": action})
        )
        return self

    def assert_api_count(self, action: str, count: int) -> "Scenario":
        """断言某 API 被调用了指定次数"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_API_COUNT,
                kwargs={"action": action, "count": count},
            )
        )
        return self

    def assert_that(
        self, predicate: Callable[["TestHarness"], None], desc: str = ""
    ) -> "Scenario":
        """自定义断言：predicate 接收 harness，可抛出 AssertionError"""
        self._steps.append(
            _Step(
                kind=_StepKind.ASSERT_CUSTOM,
                kwargs={"predicate": predicate, "desc": desc},
            )
        )
        return self

    # ---- 重置 ----

    def reset_api(self) -> "Scenario":
        """清空 API 调用记录"""
        self._steps.append(_Step(kind=_StepKind.RESET_API))
        return self

    # ---- 执行 ----

    async def run(self, harness: "TestHarness") -> None:
        """按步骤执行全部场景"""
        for i, step in enumerate(self._steps):
            step_desc = f"[{self._name}] step {i + 1}: {step.kind.name}"
            try:
                await self._execute_step(harness, step)
            except AssertionError as e:
                raise AssertionError(f"{step_desc} 失败: {e}") from e

    async def _execute_step(self, harness: "TestHarness", step: _Step) -> None:
        kw = step.kwargs

        if step.kind == _StepKind.INJECT:
            await harness.inject(kw["event"])

        elif step.kind == _StepKind.SETTLE:
            await harness.settle(kw["delay"])

        elif step.kind == _StepKind.ASSERT_API_CALLED:
            action = kw["action"]
            assert harness.api_called(action), (
                f"期望 API '{action}' 被调用，但未找到调用记录"
            )
            match = kw.get("match", {})
            if match:
                calls = harness.get_api_calls(action)
                matched = False
                for call in calls:
                    if all(
                        k in call.kwargs and call.kwargs[k] == v
                        for k, v in match.items()
                    ):
                        matched = True
                        break
                assert matched, f"API '{action}' 被调用但参数不匹配: 期望包含 {match}"

        elif step.kind == _StepKind.ASSERT_API_NOT_CALLED:
            action = kw["action"]
            assert not harness.api_called(action), (
                f"期望 API '{action}' 未被调用，但实际被调用了"
            )

        elif step.kind == _StepKind.ASSERT_API_COUNT:
            action = kw["action"]
            expected = kw["count"]
            actual = harness.api_call_count(action)
            assert actual == expected, (
                f"API '{action}' 调用次数: 期望 {expected}，实际 {actual}"
            )

        elif step.kind == _StepKind.ASSERT_CUSTOM:
            kw["predicate"](harness)

        elif step.kind == _StepKind.RESET_API:
            harness.reset_api()
