"""adapter 命令 — 适配器管理（全副屏交互）。"""

import sys
from typing import Any, Dict, List, Optional

import click

from ..utils.checkbox import _is_raw_terminal, _read_key
from ..utils.colors import success, warning, info, header

# ---------------------------------------------------------------------------
# ANSI escape sequences
# ---------------------------------------------------------------------------

_ENTER_ALT = "\033[?1049h"
_LEAVE_ALT = "\033[?1049l"
_CLEAR = "\033[2J"
_HOME = "\033[H"
_HIDE_CUR = "\033[?25l"
_SHOW_CUR = "\033[?25h"

_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"
_DIM = "\033[2m"
_BOLD = "\033[1m"
_RESET = "\033[0m"


# ---------------------------------------------------------------------------
# 辅助：从注册表 + 已有配置构建交互列表
# ---------------------------------------------------------------------------


def _get_registry():
    from ncatbot.adapter import adapter_registry

    return adapter_registry


def _get_manager():
    from ncatbot.utils import get_config_manager

    return get_config_manager()


def _build_items(
    existing_adapters: Optional[list] = None,
) -> List[Dict[str, Any]]:
    """合并注册表与已有配置，构建交互列表。

    每项含：name / cls / platform / description / enabled / config / configured。
    """
    registry = _get_registry()
    available = registry.discover()

    existing_map: Dict[str, Any] = {}
    if existing_adapters:
        for entry in existing_adapters:
            t = entry.get("type") if isinstance(entry, dict) else entry.type
            existing_map[t] = entry

    items: List[Dict[str, Any]] = []
    for name in sorted(available.keys()):
        if name == "mock":
            continue
        cls = available[name]
        existing = existing_map.get(name)

        enabled = False
        config: Dict[str, Any] = {}
        if existing is not None:
            if isinstance(existing, dict):
                enabled = existing.get("enabled", True)
                config = existing.get("config", {})
            else:
                enabled = existing.enabled
                config = (
                    dict(existing.config)
                    if not isinstance(existing.config, dict)
                    else existing.config
                )

        items.append(
            {
                "name": name,
                "cls": cls,
                "platform": getattr(cls, "platform", name),
                "description": getattr(cls, "description", name),
                "enabled": enabled,
                "config": config,
                "configured": bool(config),
            }
        )
    return items


# ---------------------------------------------------------------------------
# 渲染
# ---------------------------------------------------------------------------


def _render(items: List[Dict[str, Any]], cursor: int) -> str:
    """渲染适配器管理画面。"""
    lines: list[str] = []
    lines.append(f"{_CYAN}{_BOLD}── 适配器管理 ──{_RESET}")
    lines.append(f"{_DIM}  ↑/↓ 移动  空格 启用/禁用  Enter 配置  q 保存退出{_RESET}")
    lines.append("")

    for idx, item in enumerate(items):
        pointer = f"{_CYAN}❯{_RESET} " if idx == cursor else "  "
        box = f"{_GREEN}[x]{_RESET}" if item["enabled"] else "[ ]"
        desc = (
            f"{_BOLD}{item['description']}{_RESET}"
            if idx == cursor
            else item["description"]
        )

        if item["enabled"] and item["configured"]:
            status = f"  {_GREEN}● 已配置{_RESET}"
        elif item["enabled"] and not item["configured"]:
            status = f"  {_YELLOW}◐ 未配置{_RESET}"
        else:
            status = ""

        lines.append(f"{pointer}{box} {desc}{status}")

    lines.append("")
    lines.append(f"{_DIM}  启用的适配器将在 bot 启动时加载{_RESET}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 单项配置（调用适配器 cli_configure 钩子）
# ---------------------------------------------------------------------------


def _run_configure(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """在副屏中运行适配器的 cli_configure()，返回配置字典。"""
    sys.stdout.write(_SHOW_CUR + _CLEAR + _HOME)
    sys.stdout.flush()
    try:
        config = item["cls"].cli_configure()
        click.echo()
        click.pause("按任意键返回...")
        return config
    except (KeyboardInterrupt, EOFError):
        return None


# ---------------------------------------------------------------------------
# 副屏交互主循环
# ---------------------------------------------------------------------------


def adapter_interactive(
    existing_adapters: Optional[list] = None,
    *,
    default_first: bool = False,
) -> List[Dict[str, Any]]:
    """全副屏适配器管理交互。

    Parameters
    ----------
    existing_adapters:
        当前已配置的适配器条目（来自 config.yaml 或 ``None``）。
    default_first:
        若无已有配置，是否默认启用第一个适配器。

    Returns
    -------
    适配器条目字典列表，可直接序列化到 config.yaml。
    """
    items = _build_items(existing_adapters)
    if not items:
        click.echo(warning("未发现任何可用适配器"))
        return []

    if default_first and not any(i["enabled"] for i in items):
        items[0]["enabled"] = True

    # 非交互终端降级
    if not _is_raw_terminal():
        return _fallback(items)

    cursor = 0
    sys.stdout.write(_ENTER_ALT + _HIDE_CUR)
    sys.stdout.flush()

    try:
        while True:
            output = _render(items, cursor)
            sys.stdout.write(_HOME + _CLEAR + output)
            sys.stdout.flush()

            key = _read_key()
            if key == "up":
                cursor = (cursor - 1) % len(items)
            elif key == "down":
                cursor = (cursor + 1) % len(items)
            elif key == "space":
                items[cursor]["enabled"] = not items[cursor]["enabled"]
            elif key == "enter":
                config = _run_configure(items[cursor])
                if config is not None:
                    items[cursor]["config"] = config
                    items[cursor]["configured"] = bool(config)
                    items[cursor]["enabled"] = True
                sys.stdout.write(_HIDE_CUR)
                sys.stdout.flush()
            elif key in ("q", "Q", "esc"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        sys.stdout.write(_SHOW_CUR + _LEAVE_ALT)
        sys.stdout.flush()

    return _collect_results(items)


# ---------------------------------------------------------------------------
# 非交互降级
# ---------------------------------------------------------------------------


def _fallback(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    click.echo(header("可用适配器:"))
    for idx, item in enumerate(items):
        status = "已启用" if item["enabled"] else "未启用"
        click.echo(f"  {idx + 1}. [{status}] {item['description']}")

    raw = click.prompt("输入要启用的编号（逗号分隔）", default="1")
    chosen: set[int] = set()
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            val = int(part) - 1
            if 0 <= val < len(items):
                chosen.add(val)

    for idx in sorted(chosen):
        items[idx]["enabled"] = True
        config = items[idx]["cls"].cli_configure()
        items[idx]["config"] = config
        items[idx]["configured"] = bool(config)

    return _collect_results(items)


# ---------------------------------------------------------------------------
# 结果收集
# ---------------------------------------------------------------------------


def _collect_results(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从交互列表中提取需要写入配置的条目。"""
    results: List[Dict[str, Any]] = []
    for item in items:
        if item["enabled"] or item["configured"]:
            results.append(
                {
                    "type": item["name"],
                    "platform": item["platform"],
                    "enabled": item["enabled"],
                    "config": item["config"],
                }
            )
    return results


# ---------------------------------------------------------------------------
# 摘要输出
# ---------------------------------------------------------------------------


def _print_summary(results: List[Dict[str, Any]]) -> None:
    """在主终端打印适配器配置摘要。"""
    if not results:
        click.echo(info("未配置任何适配器"))
        return
    click.echo(header("适配器配置已保存:"))
    for entry in results:
        label = f"{entry['type']} ({entry['platform']})"
        if entry["enabled"]:
            click.echo(f"  {success('✔')} {label}")
        else:
            click.echo(f"  {warning('○')} {label}")


# ---------------------------------------------------------------------------
# adapter 命令入口
# ---------------------------------------------------------------------------


@click.command()
def adapter():
    """适配器管理（启用 / 禁用 / 配置）"""
    mgr = _get_manager()
    existing = mgr.config.adapters

    results = adapter_interactive(existing)

    # 写回配置
    from ncatbot.utils.config.models import AdapterEntry

    mgr.config.adapters = [AdapterEntry(**entry) for entry in results]
    mgr.save()

    _print_summary(results)
