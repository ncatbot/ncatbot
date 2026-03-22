"""run / dev 命令 — 启动 Bot。"""

import click

from .init import ensure_project_initialized


@click.command()
@click.option("--debug", is_flag=True, help="启用调试模式")
@click.option("--no-hot-reload", is_flag=True, help="禁用插件热重载")
@click.option("--plugin-dir", default="plugins", show_default=True, help="插件目录路径")
def run(debug: bool, no_hot_reload: bool, plugin_dir: str):
    """启动 NcatBot（连接 NapCat + 加载插件 + 监听事件）"""
    from ncatbot.app import BotClient

    ensure_project_initialized(".")
    bot = BotClient(debug=debug, plugin_dir=plugin_dir)
    bot.run()


@click.command()
@click.option("--plugin-dir", default="plugins", show_default=True, help="插件目录路径")
def dev(plugin_dir: str):
    """以开发模式启动（debug=True + 热重载）"""
    from ncatbot.app import BotClient

    ensure_project_initialized(".")
    bot = BotClient(debug=True, plugin_dir=plugin_dir)
    bot.run()
