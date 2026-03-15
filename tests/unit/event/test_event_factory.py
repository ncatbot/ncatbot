"""
事件实体工厂规范测试

规范:
  E-01: GroupMessageEventData → GroupMessageEvent
  E-02: PrivateMessageEventData → PrivateMessageEvent
  E-03: 未知 post_type 降级到 BaseEvent
  E-04: __getattr__ (property) 代理底层数据字段
  E-05: MessageEvent.reply() 调用 API 发消息
  E-06: GroupMessageEvent.kick() / ban() 调用正确 API
  E-07: RequestEvent.approve() / reject() 调用正确 API
"""

import pytest

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.event.factory import create_entity
from ncatbot.event.base import BaseEvent
from ncatbot.event.message import GroupMessageEvent, PrivateMessageEvent
from ncatbot.event.notice import GroupIncreaseEvent
from ncatbot.event.request import FriendRequestEvent, GroupRequestEvent
from ncatbot.testing import factory

pytestmark = pytest.mark.asyncio


# ---- E-01 / E-02: 精确映射 ----


def test_group_message_creates_group_event():
    """E-01: GroupMessageEventData → GroupMessageEvent"""
    data = factory.group_message("hi", group_id="111", user_id="222")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupMessageEvent)


def test_private_message_creates_private_event():
    """E-02: PrivateMessageEventData → PrivateMessageEvent"""
    data = factory.private_message("hi", user_id="333")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, PrivateMessageEvent)


def test_friend_request_creates_friend_request_event():
    """E-01 补充: FriendRequestEventData → FriendRequestEvent"""
    data = factory.friend_request(user_id="444")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, FriendRequestEvent)


def test_group_request_creates_group_request_event():
    """E-01 补充: GroupRequestEventData → GroupRequestEvent"""
    data = factory.group_request(user_id="555", group_id="666")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupRequestEvent)


def test_group_increase_creates_event():
    """E-01 补充: GroupIncreaseNoticeEventData → GroupIncreaseEvent"""
    data = factory.group_increase(user_id="777", group_id="888")
    entity = create_entity(data, MockBotAPI())
    assert isinstance(entity, GroupIncreaseEvent)


# ---- E-03: 降级映射 ----


def test_unknown_notice_falls_back():
    """E-03: 未精确映射的 Notice 降级到 NoticeEvent"""

    data = factory.group_ban(user_id="123", duration=600)
    entity = create_entity(data, MockBotAPI())
    # GroupBanNoticeEventData 没有精确映射，会降级
    assert isinstance(entity, BaseEvent)


# ---- E-04: property 代理 ----


def test_event_properties_proxy_data():
    """E-04: 事件实体 property 代理底层数据字段"""
    data = factory.group_message("test", group_id="111", user_id="222")
    entity = create_entity(data, MockBotAPI())

    assert entity.time == data.time
    assert entity.self_id == data.self_id
    assert isinstance(entity, GroupMessageEvent)
    assert entity.group_id == "111"
    assert entity.user_id == "222"
    assert entity.raw_message == "test"


# ---- E-05: reply() ----


async def test_message_event_reply_group():
    """E-05: GroupMessageEvent.reply() 调用 send_group_msg"""
    api = MockBotAPI()
    data = factory.group_message("hello", group_id="111", user_id="222")
    entity = create_entity(data, api)

    await entity.reply("world")
    assert api.called("send_group_msg")
    call = api.last_call("send_group_msg")
    # args: (group_id, message)
    assert call.args[0] == "111"


async def test_message_event_reply_private():
    """E-05 补充: PrivateMessageEvent.reply() 调用 send_private_msg"""
    api = MockBotAPI()
    data = factory.private_message("hello", user_id="333")
    entity = create_entity(data, api)

    await entity.reply("world")
    assert api.called("send_private_msg")
    call = api.last_call("send_private_msg")
    # args: (user_id, message)
    assert call.args[0] == "333"


# ---- E-06: kick() / ban() ----


async def test_group_message_event_kick():
    """E-06: GroupMessageEvent.kick() 调用 set_group_kick"""
    api = MockBotAPI()
    data = factory.group_message("test", group_id="111", user_id="222")
    entity = create_entity(data, api)

    await entity.kick()
    assert api.called("set_group_kick")
    call = api.last_call("set_group_kick")
    # args: (group_id, user_id, reject_add_request)
    assert call.args[0] == "111"
    assert call.args[1] == "222"


async def test_group_message_event_ban():
    """E-06: GroupMessageEvent.ban() 调用 set_group_ban"""
    api = MockBotAPI()
    data = factory.group_message("test", group_id="111", user_id="222")
    entity = create_entity(data, api)

    await entity.ban(duration=600)
    assert api.called("set_group_ban")
    call = api.last_call("set_group_ban")
    assert call.args[0] == "111"
    assert call.args[1] == "222"
    assert call.args[2] == 600


# ---- E-07: approve() / reject() ----


async def test_friend_request_approve():
    """E-07: FriendRequestEvent.approve() 调用 set_friend_add_request"""
    api = MockBotAPI()
    data = factory.friend_request(user_id="444")
    entity = create_entity(data, api)

    await entity.approve()
    assert api.called("set_friend_add_request")
    call = api.last_call("set_friend_add_request")
    # args: (flag, approve, remark)
    assert call.args[1] is True


async def test_group_request_reject():
    """E-07: GroupRequestEvent.reject() 调用 set_group_add_request"""
    api = MockBotAPI()
    data = factory.group_request(user_id="555", group_id="666")
    entity = create_entity(data, api)

    await entity.reject(reason="no")
    assert api.called("set_group_add_request")
    call = api.last_call("set_group_add_request")
    # args: (flag, sub_type, approve, reason)
    assert call.args[2] is False


async def test_message_event_delete():
    """E-05 补充: MessageEvent.delete() 调用 delete_msg"""
    api = MockBotAPI()
    data = factory.group_message("test", group_id="111")
    entity = create_entity(data, api)

    await entity.delete()
    assert api.called("delete_msg")
