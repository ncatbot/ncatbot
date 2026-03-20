"""
集成测试：08_command_group 插件
"""

import pytest
from ncatbot.types.qq import GroupMessageEventData


@pytest.mark.asyncio
async def test_admin_kick_command(harness):
    """测试 /admin kick 命令"""
    event_data = GroupMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "1",
            "group_id": "123456",
            "user_id": "100",
            "message": [],
            "raw_message": "/admin kick 789",
            "sender": {"user_id": "100", "nickname": "TestUser"},
        }
    )

    # 注入消息
    await harness.inject(event_data)
    await harness.settle()


@pytest.mark.asyncio
async def test_admin_ban_command(harness):
    """测试 /admin ban 命令"""
    event_data = GroupMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "1",
            "group_id": "123456",
            "user_id": "100",
            "message": [],
            "raw_message": "/admin ban 789 120",
            "sender": {"user_id": "100", "nickname": "TestUser"},
        }
    )

    await harness.inject(event_data)
    await harness.settle()


@pytest.mark.asyncio
async def test_calc_add_command(harness):
    """测试 /calc add 命令"""
    event_data = GroupMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "1",
            "group_id": "123456",
            "user_id": "100",
            "message": [],
            "raw_message": "/calc add 10 20",
            "sender": {"user_id": "100", "nickname": "TestUser"},
        }
    )

    await harness.inject(event_data)
    await harness.settle()


@pytest.mark.asyncio
async def test_calc_divide_command(harness):
    """测试 /calc divide 命令"""
    event_data = GroupMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "1",
            "group_id": "123456",
            "user_id": "100",
            "message": [],
            "raw_message": "/calc divide 10.5 2.5",
            "sender": {"user_id": "100", "nickname": "TestUser"},
        }
    )

    await harness.inject(event_data)
    await harness.settle()


@pytest.mark.asyncio
async def test_calc_echo_command(harness):
    """测试 /calc echo 命令"""
    event_data = GroupMessageEventData.model_validate(
        {
            "time": 1,
            "self_id": "10001",
            "post_type": "message",
            "message_type": "group",
            "sub_type": "normal",
            "message_id": "1",
            "group_id": "123456",
            "user_id": "100",
            "message": [],
            "raw_message": "/calc echo hello world",
            "sender": {"user_id": "100", "nickname": "TestUser"},
        }
    )

    await harness.inject(event_data)
    await harness.settle()
