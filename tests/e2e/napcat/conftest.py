"""
NapCat E2E 测试 conftest

配置说明:
  通过环境变量传入 NapCat 连接参数和测试目标:
    NAPCAT_WS_URI        WebSocket 地址 (默认 ws://localhost:3001)
    NAPCAT_TEST_GROUP     测试群号 (必填)
    NAPCAT_TEST_USER      测试用户 QQ (必填)
    NAPCAT_API_TIMEOUT    API 调用超时秒数 (默认 30)

  标记:
    @pytest.mark.napcat — 需要真实 NapCat 连接的测试

  运行:
    pytest tests/e2e/napcat/ -m napcat -v

  跳过:
    未设置 NAPCAT_TEST_GROUP 时自动跳过全部 napcat 标记的测试。
    连接失败时会询问是否本地安装/启动 NapCat，拒绝则跳过。
"""

import asyncio
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio

from ncatbot.adapter.napcat.connection.websocket import NapCatWebSocket
from ncatbot.adapter.napcat.connection.protocol import OB11Protocol
from ncatbot.adapter.napcat.api.bot_api import NapCatBotAPI
from ncatbot.adapter.napcat.setup.launcher import NapCatLauncher
from ncatbot.api.client import BotAPIClient


def _env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def _require_env(key: str) -> str:
    val = os.environ.get(key)
    if not val:
        pytest.skip(f"环境变量 {key} 未设置，跳过 NapCat E2E 测试")
    return val


# ── 自动跳过无配置的测试 ─────────────────────────────────────


def pytest_collection_modifyitems(items):
    """未配置 NAPCAT_TEST_GROUP 时，自动 skip 所有 napcat 标记的测试"""
    if os.environ.get("NAPCAT_TEST_GROUP"):
        return
    skip = pytest.mark.skip(reason="NAPCAT_TEST_GROUP 未设置")
    for item in items:
        if "napcat" in item.keywords:
            item.add_marker(skip)


# ── Fixtures ──────────────────────────────────────────────────


@pytest.fixture(scope="session")
def napcat_ws_uri() -> str:
    return _env("NAPCAT_WS_URI", "ws://localhost:3001")


@pytest.fixture(scope="session")
def napcat_test_group() -> str:
    return _require_env("NAPCAT_TEST_GROUP")


@pytest.fixture(scope="session")
def napcat_test_user() -> str:
    return _require_env("NAPCAT_TEST_USER")


@pytest.fixture(scope="session")
def napcat_timeout() -> float:
    return float(_env("NAPCAT_API_TIMEOUT", "30"))


async def _try_connect_or_setup(ws: NapCatWebSocket, uri: str) -> None:
    """尝试连接 WebSocket，失败时询问用户是否本地安装/启动 NapCat"""
    try:
        await ws.connect()
        return
    except (ConnectionRefusedError, OSError):
        pass

    print(f"\n⚠ 无法连接到 NapCat WebSocket 服务: {uri}")
    print("可能原因: NapCat 服务未启动或地址配置错误\n")

    answer = input("是否尝试本地安装/启动 NapCat? [y/N]: ").strip().lower()
    if answer not in ("y", "yes"):
        pytest.skip("NapCat 服务不可用，用户选择跳过")

    launcher = NapCatLauncher()
    await launcher.launch()
    await ws.connect()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def napcat_api(napcat_ws_uri: str) -> AsyncGenerator[BotAPIClient, None]:
    """创建并连接 NapCat API 客户端 (session 级别复用)"""
    ws = NapCatWebSocket(napcat_ws_uri)
    await _try_connect_or_setup(ws, napcat_ws_uri)

    protocol = OB11Protocol(ws)

    # 启动消息分发循环
    listen_task = asyncio.create_task(ws.listen(protocol.on_message))

    bot_api = NapCatBotAPI(protocol)
    client = BotAPIClient(bot_api)

    yield client

    # 清理
    protocol.cancel_all()
    listen_task.cancel()
    try:
        await listen_task
    except asyncio.CancelledError:
        pass
    await ws.disconnect()
