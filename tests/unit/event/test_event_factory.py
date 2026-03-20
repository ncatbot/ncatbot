"""
事件实体工厂规范测试

规范:
  E-01: GroupMessageEventData → GroupMessageEvent
  E-02: PrivateMessageEventData → PrivateMessageEvent
  E-03: 未知 post_type 降级到 BaseEvent
  E-04: __getattr__ (property) 代理底层数据字段
"""

from ncatbot.adapter.mock.api import MockBotAPI
from ncatbot.event.common.factory import create_entity
from ncatbot.event.common.base import BaseEvent
from ncatbot.event.qq.message import GroupMessageEvent, PrivateMessageEvent
from ncatbot.event.qq.notice import GroupIncreaseEvent
from ncatbot.event.qq.request import FriendRequestEvent, GroupRequestEvent
from ncatbot.testing import factory


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
