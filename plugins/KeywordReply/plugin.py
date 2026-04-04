from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any

from ncatbot.core import registrar
from ncatbot.event.qq import GroupMessageEvent
from ncatbot.plugin import NcatBotPlugin
from ncatbot.utils import get_config_manager

# 在默认消息链中稍后处理，避免过早消费
MESSAGE_HANDLER_PRIORITY = -30

DEFAULT_RULES: dict[str, Any] = {
    "group_whitelist": [],
    "keywords": {},
    "regex": {},
}

HELP_TEXT = """
🍊KeywordReply热管理菜单🍊
仅限管理员使用
/kw add [关键词] [回复内容] - 添加关键词回复
/kw addre [正则表达式] [回复内容] - 添加正则回复
/kw addwhite [群号] - 添加白名单群
/kw del [关键词/正则/群号] - 删除关键词/正则/白名单群
/kw list - 查看当前配置
/kw reload - 重载配置
""".strip()


class KeywordReply(NcatBotPlugin):
    name = "KeywordReply"
    version = "2.2.0"
    author = "cheng160"
    description = "群聊关键词与正则回复"

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self._rules: dict[str, Any] = copy.deepcopy(DEFAULT_RULES)
        self._regex_cache: dict[str, re.Pattern[str]] = {}

    @property
    def _rules_path(self) -> Path:
        return self._manifest.plugin_path / "config.json"

    async def on_load(self) -> None:
        self._rules = self._load_rules()
        self._rebuild_regex_cache()
        self.logger.info("%s 已加载，规则文件 %s", self.name, self._rules_path)

    def _normalize_rules(self, raw: Any) -> dict[str, Any]:
        base = copy.deepcopy(DEFAULT_RULES)
        if not isinstance(raw, dict):
            return base
        wl = raw.get("group_whitelist", [])
        base["group_whitelist"] = (
            [str(x) for x in wl] if isinstance(wl, list) else []
        )
        kw = raw.get("keywords", {})
        base["keywords"] = (
            {str(k): str(v) for k, v in kw.items()} if isinstance(kw, dict) else {}
        )
        rx = raw.get("regex", {})
        base["regex"] = (
            {str(k): str(v) for k, v in rx.items()} if isinstance(rx, dict) else {}
        )
        return base

    def _load_rules(self) -> dict[str, Any]:
        path = self._rules_path
        if not path.exists():
            path.write_text(
                json.dumps(DEFAULT_RULES, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return copy.deepcopy(DEFAULT_RULES)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            self.logger.error("读取规则文件失败，使用默认空规则: %s", e)
            return copy.deepcopy(DEFAULT_RULES)
        return self._normalize_rules(raw)

    def _save_rules(self) -> None:
        self._rules_path.write_text(
            json.dumps(self._rules, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _rebuild_regex_cache(self) -> None:
        self._regex_cache.clear()
        for pattern in self._rules["regex"]:
            try:
                self._regex_cache[pattern] = re.compile(pattern)
            except re.error:
                self.logger.warning("跳过无效正则（请在配置中修正）: %s", pattern)

    def _is_root(self, user_id: str) -> bool:
        return str(user_id) == str(get_config_manager().root)

    def _group_allowed(self, group_id: str) -> bool:
        allowed = {str(x) for x in self._rules["group_whitelist"]}
        return str(group_id) in allowed

    @registrar.qq.on_group_command("/kw", "kw")
    async def cmd_kw(
        self,
        event: GroupMessageEvent,
        action: str = "",
        key: str = "",
        reply: str = "",
    ) -> None:
        if not self._is_root(event.user_id):
            return

        action = action.strip().lower()
        reply_stripped = reply.strip()

        if action == "add":
            await self._kw_add_keyword(event, key, reply_stripped)
            return
        if action == "addre":
            await self._kw_add_regex(event, key, reply_stripped)
            return
        if action == "addwhite":
            await self._kw_add_whitelist(event, key)
            return
        if action == "del":
            await self._kw_delete(event, key)
            return
        if action == "list":
            await self._kw_list(event)
            return
        if action == "reload":
            self._rules = self._load_rules()
            self._rebuild_regex_cache()
            await event.reply("✅ 配置已重载", at_sender=False)
            return

        await event.reply(HELP_TEXT, at_sender=False)

    async def _kw_add_keyword(
        self, event: GroupMessageEvent, key: str, reply_text: str
    ) -> None:
        if not key or not reply_text:
            await event.reply("用法：/kw add [关键词] [回复内容]", at_sender=False)
            return
        self._rules["keywords"][key] = reply_text
        self._save_rules()
        await event.reply(f"✅ 关键词【{key}】已添加", at_sender=False)

    async def _kw_add_regex(
        self, event: GroupMessageEvent, pattern: str, reply_text: str
    ) -> None:
        if not pattern or not reply_text:
            await event.reply(
                "用法：/kw addre [正则表达式] [回复内容]", at_sender=False
            )
            return
        try:
            compiled = re.compile(pattern)
        except re.error:
            await event.reply("❌ 正则格式错误", at_sender=False)
            return
        self._rules["regex"][pattern] = reply_text
        self._regex_cache[pattern] = compiled
        self._save_rules()
        await event.reply(f"✅ 正则【{pattern}】已添加", at_sender=False)

    async def _kw_add_whitelist(self, event: GroupMessageEvent, group_id: str) -> None:
        if not group_id:
            await event.reply("用法：/kw addwhite [群号]", at_sender=False)
            return
        gid = str(group_id).strip()
        wl: list[str] = self._rules["group_whitelist"]
        if gid not in {str(x) for x in wl}:
            wl.append(gid)
            self._save_rules()
        await event.reply(f"✅ 白名单群【{gid}】已添加", at_sender=False)

    async def _kw_delete(self, event: GroupMessageEvent, key: str) -> None:
        if not key:
            await event.reply(
                "用法：/kw del [关键词/正则/群号]", at_sender=False
            )
            return
        keywords: dict[str, str] = self._rules["keywords"]
        if key in keywords:
            del keywords[key]
            self._save_rules()
            await event.reply(f"✅ 关键词【{key}】已删除", at_sender=False)
            return
        regexes: dict[str, str] = self._rules["regex"]
        if key in regexes:
            del regexes[key]
            self._regex_cache.pop(key, None)
            self._save_rules()
            await event.reply(f"✅ 正则【{key}】已删除", at_sender=False)
            return
        wl: list[str] = self._rules["group_whitelist"]
        if key in wl:
            wl.remove(key)
            self._save_rules()
            await event.reply(f"✅ 白名单群【{key}】已删除", at_sender=False)
            return
        await event.reply("❌ 未找到该关键词/正则/群号", at_sender=False)

    async def _kw_list(self, event: GroupMessageEvent) -> None:
        kw = list(self._rules["keywords"].keys())
        rx = list(self._rules["regex"].keys())
        wl = self._rules["group_whitelist"]
        msg = f"📋 当前配置：\n关键词：{kw}\n正则：{rx}\n白名单：{wl}"
        await event.reply(msg, at_sender=False)

    @registrar.qq.on_group_message(priority=MESSAGE_HANDLER_PRIORITY)
    async def on_group_message(self, event: GroupMessageEvent) -> None:
        gid = str(event.group_id)
        if not self._group_allowed(gid):
            return

        text = "".join(seg.text for seg in event.message.filter_text())

        keywords: dict[str, str] = self._rules["keywords"]
        for k, reply_text in keywords.items():
            if k == text:
                self.logger.info("关键词命中【%s】", k)
                await event.reply(reply_text, at_sender=False)
                return

        for pattern, reply_text in self._rules["regex"].items():
            compiled = self._regex_cache.get(pattern)
            if compiled is None:
                continue
            if compiled.search(text):
                self.logger.info("正则命中【%s】", pattern)
                await event.reply(reply_text, at_sender=False)
                return
