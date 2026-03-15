"""
场景 1: 基础信息查询 (只读, 全自动)

来源: test_legacy/e2e/api/test_scenario_basic.py

规范:
  NC-01: get_login_info 返回 user_id + nickname
  NC-02: get_friend_list 返回列表
  NC-03: get_group_list 返回列表
  NC-04: get_group_info 返回指定群信息
  NC-05: get_group_member_list 返回成员列表
  NC-06: get_stranger_info 返回指定用户信息
"""

import pytest

pytestmark = [pytest.mark.napcat, pytest.mark.asyncio(loop_scope="session")]


class TestBasicInfoScenario:
    """NC-01 ~ NC-06: 只读信息查询"""

    async def test_login_info(self, napcat_api):
        result = await napcat_api.info.get_login_info()
        assert result is not None
        assert "user_id" in result or hasattr(result, "user_id")

    async def test_friend_list(self, napcat_api):
        result = await napcat_api.info.get_friend_list()
        assert isinstance(result, list)

    async def test_group_list(self, napcat_api):
        result = await napcat_api.info.get_group_list()
        assert isinstance(result, list)

    async def test_group_info(self, napcat_api, napcat_test_group):
        result = await napcat_api.info.get_group_info(group_id=int(napcat_test_group))
        assert result is not None

    async def test_group_member_list(self, napcat_api, napcat_test_group):
        result = await napcat_api.info.get_group_member_list(
            group_id=int(napcat_test_group)
        )
        assert isinstance(result, list)

    async def test_stranger_info(self, napcat_api, napcat_test_user):
        result = await napcat_api.info.get_stranger_info(user_id=int(napcat_test_user))
        assert result is not None
