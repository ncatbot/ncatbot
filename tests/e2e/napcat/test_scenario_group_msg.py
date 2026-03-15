"""
场景 2: 群消息操作 (发送 → 查询 → 撤回)

来源: test_legacy/e2e/api/test_scenario_group_msg.py

规范:
  NC-10: 发送群文本消息并获取 message_id
  NC-11: 通过 message_id 查询消息详情
  NC-12: 撤回已发送的消息
"""

import pytest

pytestmark = [pytest.mark.napcat, pytest.mark.asyncio(loop_scope="session")]


class TestGroupMessageScenario:
    """NC-10 ~ NC-12: 群消息生命周期"""

    async def test_message_lifecycle(self, napcat_api, napcat_test_group):
        """发送 → 查询 → 撤回"""
        group_id = int(napcat_test_group)

        # 发送
        result = await napcat_api.send_group_msg(
            group_id=group_id,
            message=[
                {"type": "text", "data": {"text": "[E2E] 生命周期测试 - 即将撤回"}}
            ],
        )
        assert result is not None
        message_id = result.get("message_id") if isinstance(result, dict) else result
        assert message_id, "未获取到 message_id"

        # 查询
        msg_detail = await napcat_api.info.get_msg(message_id=int(message_id))
        assert msg_detail is not None

        # 撤回
        await napcat_api.delete_msg(message_id=int(message_id))

    async def test_send_group_text(self, napcat_api, napcat_test_group):
        """简单文本消息发送"""
        result = await napcat_api.send_group_msg(
            group_id=int(napcat_test_group),
            message=[{"type": "text", "data": {"text": "[E2E] 文本消息测试"}}],
        )
        assert result is not None
