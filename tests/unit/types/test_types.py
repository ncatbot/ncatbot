"""
Types 类型模型规范测试

规范:
  T-01: BaseEventData 自动将 int 类型 ID 强转为 str
  T-02: GroupMessageEventData 必须包含 group_id 字段
  T-03: PrivateMessageEventData 不含 group_id
  T-04: NoticeEventData 子类各含对应 notice_type
  T-05: RequestEventData 子类各含 flag 字段
"""

import pytest
from pydantic import ValidationError

from ncatbot.types import (
    BaseEventData,
    GroupMessageEventData,
    PrivateMessageEventData,
    PostType,
    MessageType,
)
from ncatbot.types.notice import (
    GroupIncreaseNoticeEventData,
    GroupBanNoticeEventData,
    GroupDecreaseNoticeEventData,
    NoticeType,
)
from ncatbot.types.request import (
    FriendRequestEventData,
    GroupRequestEventData,
    RequestType,
)


# ---- T-01: ID 强转 ----


def test_base_event_coerces_int_id_to_str():
    """T-01: BaseEventData 自动将 int 类型 *_id 字段从 int 转 str"""
    data = BaseEventData.model_validate(
        {"time": 1, "self_id": 12345, "post_type": "message"}
    )
    assert data.self_id == "12345"
    assert isinstance(data.self_id, str)


def test_base_event_keeps_str_id():
    """T-01 补充: 原本是 str 的保持不变"""
    data = BaseEventData.model_validate(
        {"time": 1, "self_id": "99999", "post_type": "message"}
    )
    assert data.self_id == "99999"


def test_extra_id_fields_coerced():
    """T-01 补充: 额外的 *_id 字段也被转换"""
    data = BaseEventData.model_validate(
        {
            "time": 1,
            "self_id": 10001,
            "post_type": "message",
            "user_id": 67890,
            "group_id": 12345,
        }
    )
    assert data.self_id == "10001"


# ---- T-02: GroupMessageEventData 必须含 group_id ----


def test_group_message_requires_group_id():
    """T-02: 缺少 group_id 时抛出 ValidationError"""
    with pytest.raises(ValidationError):
        GroupMessageEventData.model_validate(
            {
                "time": 1,
                "self_id": "10001",
                "message_type": "group",
                "sub_type": "normal",
                "message_id": "1",
                "user_id": "123",
                "message": [],
                "raw_message": "",
                "sender": {"user_id": "123", "nickname": "test"},
                # 缺少 group_id
            }
        )


def test_group_message_with_group_id():
    """T-02 补充: 提供 group_id 时正常构造"""
    data = GroupMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "1",
            "user_id": "123",
            "group_id": "456",
            "message": [],
            "raw_message": "hello",
            "sender": {
                "user_id": "123",
                "nickname": "test",
                "card": "",
                "role": "member",
            },
        }
    )
    assert data.group_id == "456"
    assert data.post_type == PostType.MESSAGE
    assert data.message_type == MessageType.GROUP


# ---- T-03: PrivateMessageEventData 不含 group_id ----


def test_private_message_no_group_id():
    """T-03: PrivateMessageEventData 不含 group_id 属性"""
    PrivateMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "message_type": "private",
            "sub_type": "friend",
            "message_id": "1",
            "user_id": "123",
            "message": [],
            "raw_message": "hello",
            "sender": {"user_id": "123", "nickname": "test"},
        }
    )
    # group_id 不是 PrivateMessageEventData 的显式字段
    assert "group_id" not in PrivateMessageEventData.model_fields


# ---- T-04: Notice 子类含对应 notice_type ----


def test_group_increase_notice_type():
    """T-04: GroupIncreaseNoticeEventData 的 notice_type 为 GROUP_INCREASE"""
    data = GroupIncreaseNoticeEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "notice_type": "group_increase",
            "sub_type": "approve",
            "group_id": "111",
            "user_id": "222",
            "operator_id": "333",
        }
    )
    assert data.notice_type == NoticeType.GROUP_INCREASE


def test_group_ban_notice_type():
    """T-04: GroupBanNoticeEventData 的 notice_type 为 GROUP_BAN"""
    data = GroupBanNoticeEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "notice_type": "group_ban",
            "sub_type": "ban",
            "group_id": "111",
            "user_id": "222",
            "operator_id": "333",
            "duration": 600,
        }
    )
    assert data.notice_type == NoticeType.GROUP_BAN


def test_group_decrease_notice_type():
    """T-04: GroupDecreaseNoticeEventData 的 notice_type 为 GROUP_DECREASE"""
    data = GroupDecreaseNoticeEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "notice_type": "group_decrease",
            "sub_type": "leave",
            "group_id": "111",
            "user_id": "222",
            "operator_id": "333",
        }
    )
    assert data.notice_type == NoticeType.GROUP_DECREASE


# ---- T-05: Request 子类含 flag ----


def test_friend_request_has_flag():
    """T-05: FriendRequestEventData 含 flag 字段"""
    data = FriendRequestEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "request_type": "friend",
            "user_id": "123",
            "comment": "请加好友",
            "flag": "flag_abc",
        }
    )
    assert data.flag == "flag_abc"
    assert data.request_type == RequestType.FRIEND


def test_group_request_has_flag():
    """T-05: GroupRequestEventData 含 flag 字段"""
    data = GroupRequestEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "request_type": "group",
            "sub_type": "add",
            "user_id": "123",
            "group_id": "456",
            "comment": "请加群",
            "flag": "flag_xyz",
        }
    )
    assert data.flag == "flag_xyz"
    assert data.request_type == RequestType.GROUP


def test_request_requires_flag():
    """T-05 补充: 缺少 flag 时 ValidationError"""
    with pytest.raises(ValidationError):
        FriendRequestEventData.model_validate(
            {
                "time": 1,
                "self_id": "10001",
                "request_type": "friend",
                "user_id": "123",
                # 缺少 flag
            }
        )
