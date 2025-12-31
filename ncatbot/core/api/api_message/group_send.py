"""
群消息发送 API

提供群消息的各种发送功能，包括文本、图片、语音、文件、音乐等。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Literal, Optional, Union

from ..utils import (
    APIComponent,
    APIReturnStatus,
    MessageAPIReturnStatus,
    get_log,
)
from .validation import validate_msg

if TYPE_CHECKING:
    from ..client import IAPIClient
    from ncatbot.core.event.message_segment.message_array import MessageArray

LOG = get_log("ncatbot.core.api.api_message.group_send")


# =============================================================================
# 群消息发送 Mixin
# =============================================================================


class GroupMessageMixin(APIComponent):
    """群消息发送相关方法"""

    async def send_group_msg(
        self, group_id: Union[str, int], message: List[dict]
    ) -> str:
        """
        发送群消息（底层接口）

        Args:
            group_id: 群号
            message: 消息内容列表

        Returns:
            str: 消息 ID
        """
        if not validate_msg(message):
            LOG.warning("消息格式验证失败，发送群聊消息取消")
            return ""

        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": message},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def post_group_array_msg(
        self, group_id: Union[str, int], msg: "MessageArray"
    ) -> str:
        """
        发送群消息（MessageArray）

        Args:
            group_id: 群号
            msg: MessageArray 消息对象

        Returns:
            str: 消息 ID
        """
        return await self.send_group_msg(group_id, msg.to_list())

    async def post_all_group_array_msg(self, msg: "MessageArray") -> List[str]:
        """
        发送消息到所有群

        ⚠️ 慎用！

        Args:
            msg: MessageArray 消息对象

        Returns:
            List[str]: 消息 ID 列表
        """
        group_id_list = await self.get_group_list()
        message_id_list = []
        for group_id in group_id_list:
            message_id = await self.post_group_array_msg(group_id, msg)
            message_id_list.append(message_id)
        return message_id_list

    async def post_group_msg(
        self,
        group_id: Union[str, int],
        text: Optional[str] = None,
        at: Optional[Union[str, int]] = None,
        reply: Optional[Union[str, int]] = None,
        image: Optional[str] = None,
        rtf: Optional["MessageArray"] = None,
    ) -> str:
        """
        发送群消息（便捷方法）

        Args:
            group_id: 群号
            text: 文本内容
            at: @某人的 QQ 号
            reply: 回复的消息 ID
            image: 图片路径/URL
            rtf: 富文本 MessageArray

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event.message_segment.message_array import MessageArray

        msg_array = MessageArray()
        if reply is not None:
            msg_array.add_reply(reply)
        if at is not None:
            msg_array.add_at(at)
        if text is not None:
            msg_array.add_text(text)
        if image is not None:
            msg_array.add_image(image)
        if rtf is not None:
            msg_array += rtf
        return await self.post_group_array_msg(group_id, msg_array)

    async def send_group_text(self, group_id: Union[str, int], text: str) -> str:
        """
        发送群文本消息（支持 CQ 码）

        Args:
            group_id: 群号
            text: 文本内容

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event.message_segment.message_array import MessageArray

        msg_array = MessageArray(text)
        return await self.post_group_array_msg(group_id, msg_array)

    async def send_group_plain_text(
        self, group_id: Union[str, int], text: str
    ) -> str:
        """
        发送群纯文本消息（不转义）

        Args:
            group_id: 群号
            text: 文本内容

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event.message_segment.message_array import MessageArray
        from ncatbot.core.event import PlainText

        msg_array = MessageArray(PlainText(text))
        return await self.post_group_array_msg(group_id, msg_array)

    async def send_group_image(self, group_id: Union[str, int], image: str) -> str:
        """
        发送群图片消息

        Args:
            group_id: 群号
            image: 图片路径/URL

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event import Image

        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": [Image(file=image).to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_group_record(self, group_id: Union[str, int], file: str) -> str:
        """
        发送群语音消息

        Args:
            group_id: 群号
            file: 语音文件路径/URL

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event import Record

        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": [Record(file=file).to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_group_dice(
        self, group_id: Union[str, int], value: int = 1
    ) -> str:
        """
        发送群骰子消息

        Args:
            group_id: 群号
            value: 骰子点数（暂不支持指定）

        Returns:
            str: 消息 ID
        """
        result = await self._request_raw(
            "/send_group_msg",
            {
                "group_id": group_id,
                "message": [{"type": "dice", "data": {"value": value}}],
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_group_rps(
        self, group_id: Union[str, int], value: int = 1
    ) -> str:
        """
        发送群猜拳消息

        Args:
            group_id: 群号
            value: 猜拳结果（暂不支持指定）

        Returns:
            str: 消息 ID
        """
        result = await self._request_raw(
            "/send_group_msg",
            {
                "group_id": group_id,
                "message": [{"type": "rps", "data": {"value": value}}],
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: Optional[str] = None,
    ) -> str:
        """
        发送群文件消息

        Args:
            group_id: 群号
            file: 文件路径/URL
            name: 文件名

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event import File

        payload = File(file=file, file_name=name).to_dict()
        result = await self._request_raw(
            "/send_group_msg",
            {"group_id": group_id, "message": [payload]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    # -------------------------------------------------------------------------
    # 占位方法（由其他 API 实现）
    # -------------------------------------------------------------------------

    async def get_group_list(self) -> List[str]:
        """获取群列表（应由 GroupAPI 实现）"""
        raise NotImplementedError("This method should be implemented by GroupAPI")
