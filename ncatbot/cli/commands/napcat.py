"""napcat 命令组 — NapCat 管理与诊断。"""

import asyncio

import click


def _get_manager():
    from ncatbot.utils.config import get_config_manager

    return get_config_manager()


@click.group()
def napcat():
    """NapCat 管理"""


@napcat.group(invoke_without_command=True)
@click.pass_context
def diagnose(ctx: click.Context):
    """NapCat 诊断工具"""
    if ctx.invoked_subcommand is None:
        # 无子命令 → 运行完整诊断
        from ncatbot.adapter.napcat.debug.diagnose import diagnose as run_diagnose

        asyncio.run(run_diagnose())


@diagnose.command()
@click.option("--uri", default=None, help="WebSocket URI（默认读取配置）")
@click.option("--token", default=None, help="WebSocket Token（默认读取配置）")
def ws(uri: str | None, token: str | None):
    """检测 NapCat WebSocket 连接"""
    if uri is None or token is None:
        mgr = _get_manager()
        uri = uri or mgr.napcat.ws_uri
        token = token if token is not None else mgr.napcat.ws_token

    from ncatbot.adapter.napcat.debug.check_ws import check_ws

    asyncio.run(check_ws(uri, token))


@diagnose.command()
@click.option("--uri", default=None, help="WebUI URI（默认读取配置）")
@click.option("--token", default=None, help="WebUI Token（默认读取配置）")
def webui(uri: str | None, token: str | None):
    """检测 NapCat WebUI 状态"""
    if uri is None or token is None:
        mgr = _get_manager()
        uri = uri or mgr.napcat.webui_uri
        token = token if token is not None else mgr.napcat.webui_token

    from ncatbot.adapter.napcat.debug.check_webui import run_checks

    run_checks(uri, token)
