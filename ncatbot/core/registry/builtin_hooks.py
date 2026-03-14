"""
内置 Hook 集合

提供常用的 BEFORE_CALL 过滤 Hook，用于事件类型筛选等。

事件字段通过 event.data 访问（Event.data: BaseEventData，extra="allow"）。
"""

from .hook import Hook, HookAction, HookContext, HookStage


class MessageTypeFilter(Hook):
    """过滤消息类型 (group / private)

    通过 event.data.message_type 判断。
    """

    stage = HookStage.BEFORE_CALL

    def __init__(self, message_type: str, *, priority: int = 100):
        self.message_type = message_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        mt = getattr(ctx.event.data, "message_type", None)
        if mt is not None and hasattr(mt, "value"):
            mt = mt.value
        if mt != self.message_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<MessageTypeFilter(type={self.message_type})>"


class PostTypeFilter(Hook):
    """过滤 post_type (message / notice / request / meta_event)"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, post_type: str, *, priority: int = 100):
        self.post_type = post_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        pt = getattr(ctx.event.data, "post_type", None)
        if pt is not None and hasattr(pt, "value"):
            pt = pt.value
        if pt != self.post_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<PostTypeFilter(type={self.post_type})>"


class SubTypeFilter(Hook):
    """过滤 sub_type"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, sub_type: str, *, priority: int = 100):
        self.sub_type = sub_type
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        st = getattr(ctx.event.data, "sub_type", None)
        if st is not None and hasattr(st, "value"):
            st = st.value
        if st != self.sub_type:
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return f"<SubTypeFilter(type={self.sub_type})>"


class SelfFilter(Hook):
    """跳过 bot 自身发出的消息 (self_id == user_id)"""

    stage = HookStage.BEFORE_CALL

    def __init__(self, *, priority: int = 200):
        self.priority = priority

    async def execute(self, ctx: HookContext) -> HookAction:
        data = ctx.event.data
        self_id = getattr(data, "self_id", None)
        user_id = getattr(data, "user_id", None)
        if self_id and user_id and str(self_id) == str(user_id):
            return HookAction.SKIP
        return HookAction.CONTINUE

    def __repr__(self) -> str:
        return "<SelfFilter>"


# 预实例化常用 Hook
group_only = MessageTypeFilter("group")
private_only = MessageTypeFilter("private")
non_self = SelfFilter()
