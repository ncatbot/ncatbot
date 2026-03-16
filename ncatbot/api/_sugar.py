"""高频消息 sugar 方法 — Mixin 供 BotAPIClient 使用"""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Union

from ncatbot.types.segment import (
    MessageArray,
    Image,
    Record,
    File,
    Forward,
    PlainText,
    Video,
)

if TYPE_CHECKING:
    from ncatbot.api.interface import IBotAPI


class MessageSugarMixin:
    """消息发送 sugar 方法

    假设宿主类有 ``_base: IBotAPI`` 属性。
    """

    _base: IBotAPI

    # ---- 便捷发送（组装 MessageArray）----

    async def post_group_msg(
        self,
        group_id: Union[str, int],
        text: Optional[str] = None,
        at: Optional[Union[str, int]] = None,
        reply: Optional[Union[str, int]] = None,
        image: Optional[Union[str, Image]] = None,
        video: Optional[Union[str, Video]] = None,
        rtf: Optional[MessageArray] = None,
    ) -> dict:
        """便捷群消息 — 关键字参数自动组装 MessageArray"""
        msg = _build_message_array(
            text=text, at=at, reply=reply, image=image, video=video, rtf=rtf
        )
        return await self._base.send_group_msg(group_id, msg.to_list())

    async def post_private_msg(
        self,
        user_id: Union[str, int],
        text: Optional[str] = None,
        reply: Optional[Union[str, int]] = None,
        image: Optional[Union[str, Image]] = None,
        video: Optional[Union[str, Video]] = None,
        rtf: Optional[MessageArray] = None,
    ) -> dict:
        """便捷私聊消息"""
        msg = _build_message_array(
            text=text, reply=reply, image=image, video=video, rtf=rtf
        )
        return await self._base.send_private_msg(user_id, msg.to_list())

    async def post_group_array_msg(
        self,
        group_id: Union[str, int],
        msg: MessageArray,
    ) -> dict:
        return await self._base.send_group_msg(group_id, msg.to_list())

    async def post_private_array_msg(
        self,
        user_id: Union[str, int],
        msg: MessageArray,
    ) -> dict:
        return await self._base.send_private_msg(user_id, msg.to_list())

    # ---- 群消息 sugar ----

    async def send_group_text(self, group_id: Union[str, int], text: str) -> dict:
        return await self.post_group_msg(group_id, text=text)

    async def send_group_plain_text(self, group_id: Union[str, int], text: str) -> dict:
        msg = MessageArray([PlainText(text=text)])
        return await self._base.send_group_msg(group_id, msg.to_list())

    async def send_group_image(
        self, group_id: Union[str, int], image: Union[str, Image]
    ) -> dict:
        return await self.post_group_msg(group_id, image=image)

    async def send_group_record(self, group_id: Union[str, int], file: str) -> dict:
        msg = MessageArray([Record(file=file)])
        return await self._base.send_group_msg(group_id, msg.to_list())

    async def send_group_file(
        self,
        group_id: Union[str, int],
        file: str,
        name: Optional[str] = None,
    ) -> dict:
        msg = MessageArray([File(file=file, file_name=name)])
        return await self._base.send_group_msg(group_id, msg.to_list())

    async def send_group_video(
        self, group_id: Union[str, int], video: Union[str, Video]
    ) -> dict:
        msg = MessageArray().add_video(video)
        return await self._base.send_group_msg(group_id, msg.to_list())

    async def send_group_sticker(
        self, group_id: Union[str, int], image: Union[str, Image]
    ) -> dict:
        """发送群动画表情（sub_type=1 的图片）"""
        img = _to_sticker(image)
        msg = MessageArray().add_image(img)
        return await self._base.send_group_msg(group_id, msg.to_list())

    # ---- 私聊消息 sugar ----

    async def send_private_text(self, user_id: Union[str, int], text: str) -> dict:
        return await self.post_private_msg(user_id, text=text)

    async def send_private_plain_text(
        self, user_id: Union[str, int], text: str
    ) -> dict:
        msg = MessageArray([PlainText(text=text)])
        return await self._base.send_private_msg(user_id, msg.to_list())

    async def send_private_image(
        self, user_id: Union[str, int], image: Union[str, Image]
    ) -> dict:
        return await self.post_private_msg(user_id, image=image)

    async def send_private_record(self, user_id: Union[str, int], file: str) -> dict:
        msg = MessageArray([Record(file=file)])
        return await self._base.send_private_msg(user_id, msg.to_list())

    async def send_private_file(
        self,
        user_id: Union[str, int],
        file: str,
        name: Optional[str] = None,
    ) -> dict:
        msg = MessageArray([File(file=file, file_name=name)])
        return await self._base.send_private_msg(user_id, msg.to_list())

    async def send_private_video(
        self, user_id: Union[str, int], video: Union[str, Video]
    ) -> dict:
        msg = MessageArray().add_video(video)
        return await self._base.send_private_msg(user_id, msg.to_list())

    async def send_private_sticker(
        self, user_id: Union[str, int], image: Union[str, Image]
    ) -> dict:
        """发送私聊动画表情（sub_type=1 的图片）"""
        img = _to_sticker(image)
        msg = MessageArray().add_image(img)
        return await self._base.send_private_msg(user_id, msg.to_list())

    async def send_private_dice(self, user_id: Union[str, int], value: int = 1) -> dict:
        return await self._base.send_private_msg(
            user_id,
            [{"type": "dice", "data": {"value": value}}],
        )

    async def send_private_rps(self, user_id: Union[str, int], value: int = 1) -> dict:
        return await self._base.send_private_msg(
            user_id,
            [{"type": "rps", "data": {"value": value}}],
        )

    # ---- 合并转发 sugar ----

    async def post_group_forward_msg(
        self,
        group_id: Union[str, int],
        forward: Forward,
    ) -> dict:
        return await self._base.send_forward_msg(
            "group",
            group_id,
            **forward.to_forward_dict(),
        )

    async def post_private_forward_msg(
        self,
        user_id: Union[str, int],
        forward: Forward,
    ) -> dict:
        return await self._base.send_forward_msg(
            "private",
            user_id,
            **forward.to_forward_dict(),
        )

    async def send_group_forward_msg_by_id(
        self,
        group_id: Union[str, int],
        message_ids: List[Union[str, int]],
    ) -> dict:
        """通过消息 ID 列表转发群消息

        逐条调用 get_msg 获取消息内容，直接通过 send_group_msg 发送。
        返回最后一条发送的结果。
        """
        result: dict = {}
        for mid in message_ids:
            msg_data = await self._base.get_msg(int(mid))
            if not msg_data:
                continue
            raw_segs = msg_data.get("message", [])
            result = await self._base.send_group_msg(group_id, raw_segs)
        return result

    async def send_private_forward_msg_by_id(
        self,
        user_id: Union[str, int],
        message_ids: List[Union[str, int]],
    ) -> dict:
        """通过消息 ID 列表转发私聊消息

        逐条调用 get_msg 获取消息内容，直接通过 send_private_msg 发送。
        返回最后一条发送的结果。
        """
        result: dict = {}
        for mid in message_ids:
            msg_data = await self._base.get_msg(int(mid))
            if not msg_data:
                continue
            raw_segs = msg_data.get("message", [])
            result = await self._base.send_private_msg(user_id, raw_segs)
        return result


def _build_message_array(
    *,
    text: Optional[str] = None,
    at: Optional[Union[str, int]] = None,
    reply: Optional[Union[str, int]] = None,
    image: Optional[Union[str, Image]] = None,
    video: Optional[Union[str, Video]] = None,
    rtf: Optional[MessageArray] = None,
) -> MessageArray:
    """从关键字参数组装 MessageArray"""
    msg = MessageArray()
    if reply is not None:
        msg.add_reply(reply)
    if at is not None:
        msg.add_at(at)
    if text is not None:
        msg.add_text(text)
    if image is not None:
        msg.add_image(image)
    if video is not None:
        msg.add_video(video)
    if rtf is not None:
        msg = msg + rtf
    return msg


def _to_sticker(image: Union[str, Image]) -> Image:
    """将 str 或 Image 转为 sub_type=1 的动画表情 Image"""
    if isinstance(image, Image):
        image.sub_type = 1
        return image
    return Image(file=image, sub_type=1)
