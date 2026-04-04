from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, List

import yaml

from ncatbot.core import registrar
from ncatbot.event.qq import PrivateMessageEvent
from ncatbot.plugin import NcatBotPlugin

# 私聊消息在默认链中靠后处理，避免抢在命令解析之前消费消息
MESSAGE_HANDLER_PRIORITY = -50

ENV_API_KEY_CANDIDATES = ("ARK_API_KEY", "VOLC_ARK_API_KEY")
ENV_BASE_URL = "VOLC_ARK_BASE_URL"
DEFAULT_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"

KEYWORD_REPLY: dict[str, str] = {
    "你好": "喵~你好！",
    "晚安": "晚安喵",
    "?": "为什么要发问号喵",
    "？": "为什么要发问号喵",
    "状态": "本喵在线喵！",
    "安": "安安喵，猜是宿柠喵",
    "安安": "安安喵，猜是宿柠喵",
}

CHAT_ON_ALIASES = frozenset({"on", "开启"})
CHAT_OFF_ALIASES = frozenset({"off", "关闭"})


def _extract_responses_text(resp: Any) -> str:
    """从 Ark responses.create 返回的 Response 中取出助手文本。"""
    err = getattr(resp, "error", None)
    if err is not None:
        msg = getattr(err, "message", None) or str(err)
        return f"接口错误：{msg}"
    status = getattr(resp, "status", None)
    if status == "failed":
        return "生成失败（状态 failed）"
    parts: List[str] = []
    for item in getattr(resp, "output", None) or []:
        if getattr(item, "type", None) != "message":
            continue
        for block in getattr(item, "content", None) or []:
            if getattr(block, "type", None) == "output_text":
                parts.append(getattr(block, "text", "") or "")
    return "".join(parts).strip()


class AutoChat(NcatBotPlugin):
    name = "AutoChat"
    version = "2.2.0"
    author = "cheng160"
    description = "关键词 + 指令控制自动对话（火山方舟 Responses API）"

    def __init__(self, **kw: Any) -> None:
        super().__init__(**kw)
        self._cooldown_seconds = 10
        self._last_reply_ts: dict[str, float] = {}
        self._pending_messages: defaultdict[str, list[str]] = defaultdict(list)
        self._auto_chat_user_ids: set[str] = set()
        self._ark: Any = None
        self._ark_client_fingerprint: str = ""

    def _merge_plugin_config_from_repo_root(self) -> None:
        """若启动时 cwd 不是项目根，ConfigManager 可能未读到仓库内 config.yaml。

        自插件目录向上查找含 ``plugin.plugin_configs.<本插件名>`` 的 config.yaml 并合并。
        """
        cur: Path = self._manifest.plugin_path
        for _ in range(10):
            candidate = cur / "config.yaml"
            if candidate.is_file():
                try:
                    with open(candidate, encoding="utf-8") as f:
                        raw = yaml.safe_load(f) or {}
                    section = (
                        (raw.get("plugin") or {}).get("plugin_configs") or {}
                    ).get(self.name)
                    if isinstance(section, dict) and section:
                        self.config.update(section)
                        self.logger.info(
                            "已从 %s 合并 plugin.plugin_configs.%s（"
                            "若长期如此，请设置环境变量 NCATBOT_CONFIG_PATH 或在项目根启动）",
                            candidate,
                            self.name,
                        )
                        return
                except Exception as e:
                    self.logger.debug("读取 %s 失败: %s", candidate, e)
                # 该目录有 config.yaml 但无本插件段时，继续向上一级找
            parent = cur.parent
            if parent == cur:
                break
            cur = parent

    async def on_load(self) -> None:
        self._merge_plugin_config_from_repo_root()
        self.init_defaults(
            {
                "volc_ark_api_key": "",
                "volc_ark_base_url": DEFAULT_BASE_URL,
                "ark_model": "deepseek-v3-1-terminus",
                "cooldown_seconds": 10,
                "max_reply_chars": 1000,
                "chat_instructions": "你是猫娘，每句结尾加「喵」。",
                "enable_web_search": True,
                "web_search_max_keyword": 2,
            }
        )
        cd = self.get_config("cooldown_seconds", 10)
        try:
            self._cooldown_seconds = max(0, int(cd))
        except (TypeError, ValueError):
            self._cooldown_seconds = 10
            self.logger.warning("cooldown_seconds 无效，已回退为 10: %r", cd)

        if not self._resolve_api_key():
            self.logger.warning(
                "未配置方舟 API 密钥：请设置环境变量 ARK_API_KEY（推荐）或 VOLC_ARK_API_KEY，"
                "或在 plugin.plugin_configs.AutoChat 中填写 volc_ark_api_key",
            )
        self.logger.info("%s 已加载", self.name)

    def _resolve_api_key(self) -> str:
        for name in ENV_API_KEY_CANDIDATES:
            v = os.environ.get(name, "").strip()
            if v:
                return v
        return (self.get_config("volc_ark_api_key") or "").strip()

    def _resolve_base_url(self) -> str:
        cfg = (self.get_config("volc_ark_base_url") or "").strip()
        if cfg:
            return cfg
        return os.environ.get(ENV_BASE_URL, DEFAULT_BASE_URL).strip()

    def _get_ark(self) -> Any:
        try:
            from volcenginesdkarkruntime import Ark
        except ModuleNotFoundError:
            return None
        key = self._resolve_api_key()
        if not key:
            return None
        base = self._resolve_base_url()
        fp = f"{key[:8]}:{base}"
        if self._ark is None or self._ark_client_fingerprint != fp:
            self._ark = Ark(base_url=base, api_key=key)
            self._ark_client_fingerprint = fp
        return self._ark

    def _build_tools(self) -> list[dict[str, Any]] | None:
        if not self.get_config("enable_web_search"):
            return None
        try:
            n = int(self.get_config("web_search_max_keyword") or 2)
        except (TypeError, ValueError):
            n = 2
        n = max(1, min(n, 8))
        return [{"type": "web_search", "max_keyword": n}]

    def _call_responses_sync(self, user_text: str) -> str:
        client = self._get_ark()
        if client is None:
            raise RuntimeError("no_client")
        model = (self.get_config("ark_model") or "deepseek-v3-1-terminus").strip()
        instructions = str(
            self.get_config("chat_instructions") or "你是猫娘，每句结尾加「喵」。"
        )
        tools = self._build_tools()
        kwargs: dict[str, Any] = {
            "model": model,
            "instructions": instructions,
            "input": [{"role": "user", "content": user_text}],
        }
        if tools:
            kwargs["tools"] = tools
        resp = client.responses.create(**kwargs)
        return _extract_responses_text(resp) or "（无文本回复）"

    @registrar.qq.on_private_command("/chat", "chat")
    async def cmd_chat(self, event: PrivateMessageEvent, action: str = "") -> None:
        uid = str(event.user_id)
        token = action.strip().lower()
        if token in CHAT_ON_ALIASES:
            self._auto_chat_user_ids.add(uid)
            await event.reply("✅已开启自动对话喵~", at_sender=False)
            return
        if token in CHAT_OFF_ALIASES:
            self._auto_chat_user_ids.discard(uid)
            self._pending_messages.pop(uid, None)
            await event.reply("❌已关闭自动对话，仅关键词生效喵~", at_sender=False)
            return
        await event.reply("用法：/chat on 或 /chat off喵~", at_sender=False)

    @registrar.qq.on_private_message(priority=MESSAGE_HANDLER_PRIORITY)
    async def on_private_message(self, event: PrivateMessageEvent) -> None:
        text = event.raw_message.strip()
        if text.startswith("/"):
            return

        uid = str(event.user_id)
        if await self._reply_if_keyword_match(uid, text):
            return

        if uid not in self._auto_chat_user_ids:
            return

        now = time.time()
        self._pending_messages[uid].append(text)
        if now - self._last_reply_ts.get(uid, 0.0) < self._cooldown_seconds:
            return

        merged = " ".join(self._pending_messages.pop(uid, []))
        if not merged:
            return
        self._last_reply_ts[uid] = now
        await self._send_auto_reply(uid, merged)

    async def _reply_if_keyword_match(self, user_id: str, text: str) -> bool:
        reply = KEYWORD_REPLY.get(text)
        if reply is None:
            return False
        await self.api.qq.send_private_text(user_id, reply)
        return True

    async def _send_auto_reply(self, user_id: str, content: str) -> None:
        try:
            import volcenginesdkarkruntime  # noqa: F401
        except ModuleNotFoundError:
            await self.api.qq.send_private_text(
                user_id,
                "AutoChat 缺少依赖：请执行 pip install --upgrade "
                '"volcengine-python-sdk[ark]"（或开启 plugin.auto_install_pip_deps 后重启）。',
            )
            return

        if not self._resolve_api_key():
            await self.api.qq.send_private_text(
                user_id,
                "未配置方舟 API Key：① 环境变量 ARK_API_KEY / VOLC_ARK_API_KEY；"
                "② 项目根 config.yaml → plugin.plugin_configs.AutoChat.volc_ark_api_key；"
                "③ 设置 NCATBOT_CONFIG_PATH 指向该 config.yaml，或在项目根目录启动 Bot。",
            )
            return

        max_chars = int(self.get_config("max_reply_chars", 1000) or 1000)

        try:
            reply = await asyncio.to_thread(self._call_responses_sync, content)
        except RuntimeError:
            await self.api.qq.send_private_text(
                user_id,
                "无法创建 Ark 客户端，请检查 SDK 与密钥配置。",
            )
            return
        except Exception as e:
            self.logger.exception("Responses API 调用失败: %s", e)
            reply = f"生成失败：{e}"

        await self.api.qq.send_private_text(user_id, reply[:max_chars])
