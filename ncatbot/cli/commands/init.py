"""init 命令 — 初始化项目结构。"""

from pathlib import Path

import click
import yaml

from ..utils.colors import success, warning, info


@click.command()
@click.option("--dir", "target_dir", default=".", help="目标目录")
def init(target_dir: str):
    """初始化 NcatBot 项目（创建 config.yaml + plugins/）"""
    target = Path(target_dir).resolve()
    config_path = target / "config.yaml"
    plugins_path = target / "plugins"

    if config_path.exists():
        click.echo(warning(f"config.yaml 已存在: {config_path}"))
        if not click.confirm("是否覆盖?"):
            click.echo(info("已跳过 config.yaml"))
            _ensure_plugins_dir(plugins_path)
            return

    bot_uin = click.prompt("请输入机器人 QQ 号", type=str)
    root = click.prompt("请输入管理员 QQ 号", type=str)

    config_data = {
        "bot_uin": bot_uin,
        "root": root,
        "debug": False,
        "napcat": {
            "ws_uri": "ws://localhost:3001",
            "ws_token": "napcat_ws",
            "webui_uri": "http://localhost:6099",
            "webui_token": "napcat_webui",
            "enable_webui": True,
        },
        "plugin": {
            "plugins_dir": "plugins",
            "load_plugin": True,
            "plugin_whitelist": [],
            "plugin_blacklist": [],
        },
    }

    target.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(
            config_data,
            f,
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=False,
        )

    click.echo(success(f"config.yaml 已创建: {config_path}"))
    _ensure_plugins_dir(plugins_path)
    click.echo()
    click.echo(info("下一步: 运行 'ncatbot run' 启动机器人"))


def _ensure_plugins_dir(path: Path):
    if not path.exists():
        path.mkdir(parents=True)
        click.echo(success(f"plugins/ 目录已创建: {path}"))
    else:
        click.echo(info(f"plugins/ 目录已存在: {path}"))
