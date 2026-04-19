"""终端交互式多选 checkbox — 纯标准库实现。

交互模式使用 **alternate screen buffer**（备用屏幕），选择完成后
自动恢复原始终端内容，不会污染 shell 历史。

用法::

    choices = checkbox_prompt(
        items=["NapCat", "Bilibili", "GitHub"],
        descriptions=["QQ 适配器", "B 站适配器", "GitHub 适配器"],
        checked=[0],          # 默认选中第 0 项
        title="请选择适配器:",
    )
    # choices → [0, 2]  用户选中的索引列表

操作：↑/↓ 或 j/k 移动光标，空格 切换选中，Enter 确认。

在不支持 raw 终端的环境（如 CI / 管道）自动降级为编号输入。

``alt_screen()`` 上下文管理器可单独使用，用于在备用屏幕中
运行任意带有 click.prompt / click.confirm 的交互流程。
"""

from __future__ import annotations

import contextlib
import sys
from typing import Generator, List, Sequence

import click


def _is_raw_terminal() -> bool:
    """判断 stdin 是否连接到真实终端且支持 raw 模式。"""
    try:
        return hasattr(sys.stdin, "fileno") and sys.stdin.isatty()
    except Exception:
        return False


# ---------------------------------------------------------------------------
# ANSI escape sequences
# ---------------------------------------------------------------------------

_ENTER_ALT_SCREEN = "\033[?1049h"
_LEAVE_ALT_SCREEN = "\033[?1049l"
_CLEAR_SCREEN = "\033[2J"
_CURSOR_HOME = "\033[H"
_HIDE_CURSOR = "\033[?25l"
_SHOW_CURSOR = "\033[?25h"

_GREEN = "\033[32m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# Alternate screen context manager
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def alt_screen() -> Generator[None, None, None]:
    """进入备用屏幕缓冲区，退出时自动恢复原始终端内容。

    在 ``with`` 块内可任意使用 ``click.echo`` / ``click.prompt`` 等，
    所有输出都在备用屏幕进行，退出后原始 shell 内容完整保留。

    非交互终端下退化为无操作。
    """
    if not _is_raw_terminal():
        yield
        return

    sys.stdout.write(_ENTER_ALT_SCREEN + _CLEAR_SCREEN + _CURSOR_HOME)
    sys.stdout.flush()
    try:
        yield
    finally:
        sys.stdout.write(_LEAVE_ALT_SCREEN)
        sys.stdout.flush()


# ---------------------------------------------------------------------------
# Fallback：纯文本编号输入
# ---------------------------------------------------------------------------


def _fallback_prompt(
    items: Sequence[str],
    descriptions: Sequence[str] | None,
    checked: Sequence[int],
    title: str,
) -> List[int]:
    """非交互环境降级：打印列表让用户输入编号。"""
    click.echo(click.style(title, fg="cyan", bold=True))
    for idx, label in enumerate(items):
        marker = "*" if idx in checked else " "
        line = f"  {idx + 1}. [{marker}] {label}"
        if descriptions and idx < len(descriptions):
            line += click.style(f"  {descriptions[idx]}", dim=True)
        click.echo(line)

    raw = click.prompt(
        "\n输入编号（逗号分隔，直接回车使用默认选中项）",
        default=",".join(str(i + 1) for i in checked),
        show_default=True,
    )
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            val = int(part) - 1
            if 0 <= val < len(items):
                result.append(val)
    return result or list(checked)


# ---------------------------------------------------------------------------
# Interactive checkbox (alternate screen)
# ---------------------------------------------------------------------------


def _read_key() -> str:
    """读取单个按键（含方向键序列），返回标识字符串。"""
    if sys.platform == "win32":
        import msvcrt

        ch = msvcrt.getwch()
        if ch in ("\x00", "\xe0"):
            code = msvcrt.getwch()
            if code == "H":
                return "up"
            if code == "P":
                return "down"
            return "esc"
        if ch in ("\r", "\n"):
            return "enter"
        if ch == " ":
            return "space"
        if ch in ("k", "K"):
            return "up"
        if ch in ("j", "J"):
            return "down"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch

    import tty
    import termios

    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == "\x1b":
            seq = sys.stdin.read(2)
            if seq == "[A":
                return "up"
            if seq == "[B":
                return "down"
            return "esc"
        if ch in ("\r", "\n"):
            return "enter"
        if ch == " ":
            return "space"
        if ch in ("k", "K"):
            return "up"
        if ch in ("j", "J"):
            return "down"
        if ch == "\x03":
            raise KeyboardInterrupt
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _render_full(
    items: Sequence[str],
    descriptions: Sequence[str] | None,
    selected: List[bool],
    cursor: int,
    title: str,
) -> str:
    """渲染完整 checkbox 画面（用于备用屏幕整屏重绘）。"""
    lines: list[str] = []
    lines.append(f"{_CYAN}{_BOLD}{title}{_RESET}")
    lines.append(f"{_DIM}  ↑/↓ 移动  空格 切换  Enter 确认{_RESET}")
    lines.append("")
    for idx, label in enumerate(items):
        is_cursor = idx == cursor
        is_checked = selected[idx]
        pointer = f"{_CYAN}❯{_RESET} " if is_cursor else "  "
        box = f"{_GREEN}[x]{_RESET}" if is_checked else "[ ]"
        text = f"{_BOLD}{label}{_RESET}" if is_cursor else label
        line = f"{pointer}{box} {text}"
        if descriptions and idx < len(descriptions):
            line += f"  {_DIM}{descriptions[idx]}{_RESET}"
        lines.append(line)
    return "\n".join(lines)


def checkbox_prompt(
    items: Sequence[str],
    *,
    descriptions: Sequence[str] | None = None,
    checked: Sequence[int] | None = None,
    title: str = "请选择:",
) -> List[int]:
    """交互式 checkbox 多选提示，返回选中项的索引列表。

    交互模式在备用屏幕中运行，确认后恢复原始终端内容。

    Parameters
    ----------
    items:
        选项标签列表。
    descriptions:
        各选项的附加描述（可选）。
    checked:
        默认选中的索引列表。
    title:
        提示标题。

    Returns
    -------
    选中项的索引列表（按原始顺序）。
    """
    if not items:
        return []

    checked_set = set(checked or [])

    if not _is_raw_terminal():
        return _fallback_prompt(items, descriptions, list(checked_set), title)

    selected = [i in checked_set for i in range(len(items))]
    cursor = 0

    # 进入备用屏幕
    sys.stdout.write(_ENTER_ALT_SCREEN + _HIDE_CURSOR)
    sys.stdout.flush()

    try:
        while True:
            # 整屏重绘：光标归位 + 清屏 + 渲染
            output = _render_full(items, descriptions, selected, cursor, title)
            sys.stdout.write(_CURSOR_HOME + _CLEAR_SCREEN + output)
            sys.stdout.flush()

            key = _read_key()
            if key == "up":
                cursor = (cursor - 1) % len(items)
            elif key == "down":
                cursor = (cursor + 1) % len(items)
            elif key == "space":
                selected[cursor] = not selected[cursor]
            elif key == "enter":
                break
            elif key == "esc":
                break

    except KeyboardInterrupt:
        pass
    finally:
        # 离开备用屏幕，恢复原始内容
        sys.stdout.write(_SHOW_CURSOR + _LEAVE_ALT_SCREEN)
        sys.stdout.flush()

    return [i for i, v in enumerate(selected) if v]
