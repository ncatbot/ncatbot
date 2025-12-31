"""
私聊消息发送 API

提供私聊消息的各种发送功能，包括文本、图片、语音、文件等。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from ..utils import (
    APIComponent,
    MessageAPIReturnStatus,
    get_log,
)
from .validation import validate_msg

if TYPE_CHECKING:
    from ..client import IAPIClient
    from ncatbot.core.event.message_segment.message_array import MessageArray

LOG = get_log("ncatbot.core.api.api_message.private_send")


# =============================================================================
# 私聊消息发送 Mixin
# =============================================================================


class PrivateMessageMixin(APIComponent):
    """私聊消息发送相关方法"""

    async def send_private_msg(
        self, user_id: Union[str, int], message: List[dict]
    ) -> str:
        """
        发送私聊消息（底层接口）

        Args:
            user_id: 用户 QQ 号
            message: 消息内容列表

        Returns:
            str: 消息 ID
        """
        if not validate_msg(message):
            LOG.warning("消息格式验证失败，发送私聊消息取消")
            return ""

        result = await self._request_raw(
            "/send_private_msg",
            {"user_id": user_id, "message": message},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def post_private_array_msg(
        self, user_id: Union[str, int], msg: "MessageArray"
    ) -> str:
        """
        发送私聊消息（MessageArray）

        Args:
            user_id: 用户 QQ 号
            msg: MessageArray 消息对象

        Returns:
            str: 消息 ID
        """
        return await self.send_private_msg(user_id, msg.to_list())

    async def post_private_msg(
        self,
        user_id: Union[str, int],
        text: Optional[str] = None,
        reply: Optional[Union[str, int]] = None,
        image: Optional[str] = None,
        rtf: Optional["MessageArray"] = None,
    ) -> str:
        """
        发送私聊消息（便捷方法）

        Args:
            user_id: 用户 QQ 号
            text: 文本内容
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
        if text is not None:
            msg_array.add_text(text)
        if image is not None:
            msg_array.add_image(image)
        if rtf is not None:
            msg_array += rtf
        return await self.post_private_array_msg(user_id, msg_array)

    async def send_private_text(self, user_id: Union[str, int], text: str) -> str:
        """
        发送私聊文本消息（支持 CQ 码）

        Args:
            user_id: 用户 QQ 号
            text: 文本内容

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event.message_segment.message_array import MessageArray

        msg_array = MessageArray(text)
        return await self.post_private_array_msg(user_id, msg_array)

    async def send_private_plain_text(
        self, user_id: Union[str, int], text: str
    ) -> str:
        """
        发送私聊纯文本消息（不转义）

        Args:
            user_id: 用户 QQ 号
            text: 文本内容

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event.message_segment.message_array import MessageArray
        from ncatbot.core.event import PlainText

        msg_array = MessageArray(PlainText(text))
        return await self.post_private_array_msg(user_id, msg_array)

    async def send_private_image(self, user_id: Union[str, int], image: str) -> str:
        """
        发送私聊图片消息

        Args:
            user_id: 用户 QQ 号
            image: 图片路径/URL

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event import Image

        result = await self._request_raw(
            "/send_private_msg",
            {"user_id": user_id, "message": [Image(file=image).to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_private_record(self, user_id: Union[str, int], file: str) -> str:
        """
        发送私聊语音消息

        Args:
            user_id: 用户 QQ 号
            file: 语音文件路径/URL

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event import Record

        result = await self._request_raw(
            "/send_private_msg",
            {"user_id": user_id, "message": [Record(file=file).to_dict()]},
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_private_dice(
        self, user_id: Union[str, int], value: int = 1
    ) -> str:
        """
        发送私聊骰子消息

        Args:
            user_id: 用户 QQ 号
            value: 骰子点数（暂不支持指定）

        Returns:
            str: 消息 ID
        """
        result = await self._request_raw(
            "/send_private_msg",
            {
                "user_id": user_id,
                "message": [{"type": "dice", "data": {"value": value}}],
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_private_rps(
        self, user_id: Union[str, int], value: int = 1
    ) -> str:
        """
        发送私聊猜拳消息

        Args:
            user_id: 用户 QQ 号
            value: 猜拳结果（暂不支持指定）

        Returns:
            str: 消息 ID
        """
        result = await self._request_raw(
            "/send_private_msg",
            {
                "user_id": user_id,
                "message": [{"type": "rps", "data": {"value": value}}],
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id

    async def send_private_file(
        self,
        user_id: Union[str, int],
        file: str,
        name: Optional[str] = None,
    ) -> str:
        """
        发送私聊文件消息

        Args:
            user_id: 用户 QQ 号
            file: 文件路径/URL
            name: 文件名

        Returns:
            str: 消息 ID
        """
        from ncatbot.core.event import File

        result = await self._request_raw(
            "/send_private_msg",
            {
                "user_id": user_id,
                "message": [File(file=file, file_name=name).to_dict()],
            },
        )
        status = MessageAPIReturnStatus(result)
        return status.message_id
