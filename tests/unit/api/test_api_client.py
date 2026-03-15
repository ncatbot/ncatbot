"""
BotAPIClient 规范测试

规范:
  A-01: 高频方法平铺可直接调用
  A-02: manage 命名空间包含群管操作
  A-03: info 命名空间包含查询操作
  A-04: __getattr__ 兜底透传未定义方法
"""

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.api.client import BotAPIClient

pytestmark = pytest.mark.asyncio


@pytest.fixture
def client():
    mock = MockBotAPI()
    return BotAPIClient(mock), mock


# ---- A-01: 高频方法平铺 ----


async def test_send_group_msg(client):
    """A-01: client.send_group_msg() 可直接调用"""
    api, mock = client
    mock.set_response("send_group_msg", {"message_id": "1"})
    result = await api.send_group_msg("12345", [])
    assert result == {"message_id": "1"}
    assert mock.called("send_group_msg")


async def test_send_private_msg(client):
    """A-01: client.send_private_msg() 可直接调用"""
    api, mock = client
    await api.send_private_msg("99999", [])
    assert mock.called("send_private_msg")


async def test_delete_msg(client):
    """A-01: client.delete_msg() 可直接调用"""
    api, mock = client
    await api.delete_msg("1001")
    assert mock.called("delete_msg")


# ---- A-02: manage 命名空间 ----


async def test_manage_namespace_exists(client):
    """A-02: client.manage 属性存在"""
    api, _ = client
    assert hasattr(api, "manage")


# ---- A-03: info 命名空间 ----


async def test_info_namespace_exists(client):
    """A-03: client.info 属性存在"""
    api, _ = client
    assert hasattr(api, "info")


# ---- A-04: __getattr__ 兜底 ----


async def test_getattr_fallback(client):
    """A-04: 未定义的方法透传到底层 API"""
    api, mock = client
    # MockBotAPI 的 _record 方法通过 __getattr__ 拦截
    # 访问 mock 上不存在的已知方法
    assert hasattr(api, "send_forward_msg")
