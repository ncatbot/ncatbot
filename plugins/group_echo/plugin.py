"""群聊复读：白名单群内，相邻发言者为不同用户且文案连续相同时，满 min_chain 条则复读一次。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_config_manager

# 略靠后，减少与其它群消息插件冲突
_PRIORITY = -35


class GroupEcho(NcatBotPlugin):
    name = "group_echo"
    version = "1.0.0"
    author = "cheng160"
    description = "群聊白名单内，不同人连续发相同文本时复读一次"

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self._whitelist: set[str] = set()
        self._min_chain = 2
        # 群号 -> (当前连续文案, 已参与链的用户 id 序列表，相邻必不同)
        self._streak: dict[str, tuple[str, list[str]]] = {}

    @property
    def _config_path(self) -> Path:
        return self._manifest.plugin_path / "config.json"

    async def on_load(self) -> None:
        path = self._config_path
        if not path.exists():
            path.write_text(
                '{"group_whitelist": [], "min_chain": 2}',
                encoding="utf-8",
            )
        raw = json.loads(path.read_text(encoding="utf-8"))
        wl = raw.get("group_whitelist") or []
        self._whitelist = {str(x) for x in wl} if isinstance(wl, list) else set()
        try:
            n = int(raw.get("min_chain", 2))
            self._min_chain = max(2, n)
        except (TypeError, ValueError):
            self._min_chain = 2
        self.logger.info(
            "group_echo 已加载：白名单 %d 个群，触发链长 %d",
            len(self._whitelist),
            self._min_chain,
        )

    @registrar.qq.on_group_message(priority=_PRIORITY)
    async def on_group_message(self, event: GroupMessageEvent) -> None:
        uid = str(event.user_id)
        if uid == str(get_config_manager().config.bot_uin):
            return

        gid = str(event.group_id)
        if gid not in self._whitelist:
            return

        text = "".join(seg.text for seg in event.message.filter_text()).strip()
        if not text:
            return

        prev_text, chain = self._streak.get(gid, ("", []))

        if text != prev_text:
            self._streak[gid] = (text, [uid])
            return

        if chain and uid == chain[-1]:
            self._streak[gid] = (text, [uid])
            return

        chain = [*chain, uid]
        self._streak[gid] = (text, chain)

        if len(chain) < self._min_chain:
            return

        self._streak[gid] = ("", [])
        await event.reply(text=text, at_sender=False)
