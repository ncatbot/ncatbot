"""
BotAPIClient 规范测试

规范:
  A-01: query 命名空间包含查询操作
  A-02: __getattr__ 兆底透传未定义平台
"""

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.api.client import BotAPIClient
from ncatbot.api.qq import QQAPIClient


@pytest.fixture
def client():
    mock = MockBotAPI()
    api = BotAPIClient()
    api.register_platform("qq", QQAPIClient(mock))
    return api, mock


# ---- A-01: query 命名空间 ----


def test_query_namespace_exists(client):
    """A-01: api.qq.query 属性存在"""
    api, _ = client
    assert hasattr(api.qq, "query")


# ---- A-02: 未注册平台 ----


def test_unregistered_platform_raises(client):
    """A-02: 访问未注册的平台抛出 KeyError"""
    api, _ = client
    with pytest.raises(KeyError):
        api.platform("telegram")
