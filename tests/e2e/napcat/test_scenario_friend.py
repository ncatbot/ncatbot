"""
场景 3: 好友互动

来源: test_legacy/e2e/api/test_scenario_friend.py

规范:
  NC-20: 发送私聊文本消息
  NC-21: 发送戳一戳 (poke)
"""

import pytest

pytestmark = [pytest.mark.napcat, pytest.mark.asyncio(loop_scope="session")]


class TestFriendInteractionScenario:
    """NC-20 ~ NC-21: 好友互动操作"""

    async def test_send_private_msg(self, napcat_api, napcat_test_user):
        result = await napcat_api.send_private_msg(
            user_id=int(napcat_test_user),
            message=[{"type": "text", "data": {"text": "[E2E] 私聊消息测试"}}],
        )
        assert result is not None
