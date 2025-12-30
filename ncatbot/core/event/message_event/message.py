from typing import Union, Literal, TYPE_CHECKING, Optional, Any, Dict
from abc import abstractmethod, ABC
from ....utils import status
from ..sender import PrivateSender, GroupSender
from ..base_event import MessageEventData

if TYPE_CHECKING:
    from .message_segment import MessageArray


class BaseMessageEvent(MessageEventData, ABC):
    message_type: Optional[Literal["private", "group"]] = None  # 上级会获取
    sub_type: Optional[str] = None  # 下级会细化 Literal, 上级会获取

    def is_group_msg(self):
        return hasattr(self, "group_id")

    @abstractmethod
    async def reply(self, *args: Any, **kwargs: Any) -> Any:
        pass

    @abstractmethod
    def reply_sync(self, *args: Any, **kwargs: Any) -> Any:
        pass

    def get_core_properties_str(self):
        return super().get_core_properties_str() + [
            f"sender={self.sender}",
        ]


class AnonymousMessage(BaseMessageEvent):
    id: Optional[str] = None
    name: Optional[str] = None
    flag: Optional[str] = None

    def __init__(self, data: Dict[str, Any]):
        self.id = str(data.get("id")) if data.get("id") else None
        self.name = data.get("name")
        self.flag = data.get("flag")
    
    async def reply(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()
    
    def reply_sync(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError()


class GroupMessageEvent(BaseMessageEvent):
    message_type: Optional[Literal["group"]] = None  # 上级会获取
    anonymous: Optional[AnonymousMessage] = None
    group_id: Optional[str] = None
    sub_type: Optional[Literal["normal", "anonymous", "notice"]] = None  # 上级会获取
    sender: Optional[GroupSender] = None

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.sender = GroupSender(data.get("sender"))
        self.anonymous = (
            AnonymousMessage(data.get("anonymous"))
            if data.get("anonymous", None)
            else None
        )
        self.group_id = str(data.get("group_id"))

    def get_core_properties_str(self):
        return super().get_core_properties_str() + [f"group_id={self.group_id}"]

    async def delete(self):
        return await status.global_api.delete_msg(self.message_id)

    def delete_sync(self):
        return status.global_api.delete_msg_sync(self.message_id)

    async def kick(self):
        return await status.global_api.set_group_kick(self.group_id, self.user_id)

    def kick_sync(self):
        return status.global_api.set_group_kick_sync(self.group_id, self.user_id)

    async def ban(self, ban_duration: int = 30):
        """禁言消息发送者(秒)"""
        return await status.global_api.set_group_ban(
            self.group_id, self.user_id, ban_duration
        )

    def ban_sync(self, ban_duration: int = 30):
        return status.global_api.set_group_ban_sync(
            self.group_id, self.user_id, ban_duration
        )

    async def reply(
        self,
        text: Optional[str] = None,
        image: Optional[str] = None,
        at: bool = True,
        space: bool = True,
        rtf: Optional["MessageArray"] = None,
    ) -> Any:
        if text is not None:
            text = (" " if space else "") + text
        return await status.global_api.post_group_msg(
            self.group_id,
            text,
            self.user_id if at else None,
            reply=self.message_id,
            image=image,
            rtf=rtf,
        )

    def reply_sync(
        self,
        text: Optional[str] = None,
        image: Optional[str] = None,
        at: bool = True,
        space: bool = True,
        rtf: Optional["MessageArray"] = None,
    ) -> Any:
        if text is not None:
            text = (" " if space else "") + text
        return status.global_api.post_group_msg_sync(
            self.group_id,
            text,
            self.user_id if at else None,
            reply=self.message_id,
            image=image,
            rtf=rtf,
        )


class PrivateMessageEvent(BaseMessageEvent):
    message_type: Optional[Literal["private"]] = None  # 上级会获取
    sub_type: Optional[Literal["friend", "group", "other"]] = None  # 上级会获取
    sender: Optional[PrivateSender] = None

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.sender = PrivateSender(data.get("sender"))

    async def reply(
        self, text: Optional[str] = None, image: Optional[str] = None, rtf: Optional["MessageArray"] = None
    ) -> Any:
        return await status.global_api.post_private_msg(
            self.user_id, text, self.message_id, image, rtf
        )

    def reply_sync(
        self, text: Optional[str] = None, image: Optional[str] = None, rtf: Optional["MessageArray"] = None
    ) -> Any:
        return status.global_api.post_private_msg_sync(
            self.user_id, text, self.message_id, image, rtf
        )

    def __repr__(self):
        return super().__repr__()


class MessageSentEvent(BaseMessageEvent):
    message_type: Optional[Literal["group", "private"]] = None  # 上级会获取
    sub_type: Optional[Literal["friend", "group", "other", "normal"]] = None  # 上级会获取
    sender: Optional[Union[PrivateSender, GroupSender]] = None
    message_sent_type: Optional[Literal["self"]] = None
    target_id: Optional[str] = None
    real_seq: Optional[str] = None
    group_id: Optional[str] = None

    def __init__(self, data: Dict[str, Any]):
        super().__init__(data)
        self.message_sent_type = data.get("message_sent_type")
        self.target_id = str(data.get("target_id")) if data.get("target_id") else None
        self.real_seq = str(data.get("real_seq")) if data.get("real_seq") else None

        # 根据消息类型初始化不同的 Sender
        sender_data = data.get("sender")
        if self.message_type == "group" and sender_data:
            self.sender = GroupSender(sender_data)
            self.group_id = str(data.get("group_id")) if data.get("group_id") else None
        elif self.message_type == "private" and sender_data:
            self.sender = PrivateSender(sender_data)
        else:
            self.sender = None

    def is_group_msg(self):
        """
        判断是否为群组消息
        """
        return self.message_type == "group"

    def is_private_msg(self):
        """
        判断是否为私聊消息
        """
        return self.message_type == "private"

    def get_core_properties_str(self):
        """
        获取核心属性字符串表示
        """
        base_props = super().get_core_properties_str()
        if self.is_group_msg():
            base_props.append(f"group_id={self.group_id}")
        base_props.extend(
            [
                f"message_sent_type={self.message_sent_type}",
                f"target_id={self.target_id}",
            ]
        )
        return base_props

    async def reply(
        self, text: Optional[str] = None, image: Optional[str] = None, rtf: Optional["MessageArray"] = None
    ) -> Any:
        if self.is_group_msg():
            return await status.global_api.post_group_msg(
                group_id=self.group_id,
                text=text,
                reply=self.message_id,
                image=image,
                rtf=rtf,
            )
        elif self.is_private_msg():
            return await status.global_api.post_private_msg(
                user_id=self.user_id,
                text=text,
                reply=self.message_id,
                image=image,
                rtf=rtf,
            )

    def reply_sync(
        self, text: Optional[str] = None, image: Optional[str] = None, rtf: Optional["MessageArray"] = None
    ) -> Any:
        if self.is_group_msg():
            return status.global_api.post_group_msg_sync(
                group_id=self.group_id,
                text=text,
                reply=self.message_id,
                image=image,
                rtf=rtf,
            )
        elif self.is_private_msg():
            return status.global_api.post_private_msg_sync(
                user_id=self.user_id,
                text=text,
                reply=self.message_id,
                image=image,
                rtf=rtf,
            )

    async def delete(self):
        """
        撤回消息
        """
        return await status.global_api.delete_msg(self.message_id)

    def delete_sync(self):
        """
        撤回消息
        """
        return status.global_api.delete_msg_sync(self.message_id)

    def __repr__(self):
        return super().__repr__()
