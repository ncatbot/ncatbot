"""ncatbot test-ui — 启动测试 WebUI"""

import asyncio

import click


@click.command("test-ui")
@click.option("--port", default=8765, help="WebUI 服务端口")
@click.option("--plugins", default=None, help="要加载的插件列表（逗号分隔）")
@click.option("--dev", is_flag=True, help="开发模式（代理 Vite dev server）")
def test_ui(port: int, plugins: str | None, dev: bool):
    """启动测试 WebUI"""
    from ncatbot.webui.server import start_webui

    plugin_list = (
        [p.strip() for p in plugins.split(",") if p.strip()] if plugins else None
    )
    asyncio.run(start_webui(port=port, plugins=plugin_list, dev=dev))
