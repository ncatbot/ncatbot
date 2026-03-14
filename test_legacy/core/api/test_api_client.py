"""
API 模块单元测试

测试 APIResponse、MockAPIClient、BotAPI.from_client 等核心组件。
"""

from ncatbot.core.api.client import APIResponse


class TestAPIResponse:
    """APIResponse 数据类测试"""

    def test_from_dict_success(self):
        """测试成功响应的解析"""
        data = {
            "retcode": 0,
            "message": "ok",
            "data": {"user_id": 12345, "nickname": "test"},
        }
        response = APIResponse.from_dict(data)

        assert response.retcode == 0
        assert response.message == "ok"
        assert response.data == {"user_id": 12345, "nickname": "test"}
        assert response.raw == data
        assert response.is_success is True
        assert bool(response) is True

    def test_from_dict_error(self):
        """测试错误响应的解析"""
        data = {
            "retcode": 100,
            "message": "参数错误",
            "data": None,
        }
        response = APIResponse.from_dict(data)

        assert response.retcode == 100
        assert response.message == "参数错误"
        assert response.data is None
        assert response.is_success is False
        assert bool(response) is False

    def test_from_dict_missing_fields(self):
        """测试缺少字段时的默认值"""
        data = {}
        response = APIResponse.from_dict(data)

        assert response.retcode == -1
        assert response.message == ""
        assert response.data is None

    def test_from_dict_partial_fields(self):
        """测试部分字段缺失"""
        data = {"retcode": 0}
        response = APIResponse.from_dict(data)

        assert response.retcode == 0
        assert response.message == ""
        assert response.data is None
