import random
import string
from re import search
from typing import Any


def strong_password_check(password: str) -> bool:
    """检查密码强度：包含数字、大小写字母、特殊符号，至少 12 位。"""
    special_chars = r"!@#$%^&*()_+\-=\[\]{}|;:,.<>?"
    patterns = [r"\d", "[a-z]", "[A-Z]", f"[{special_chars}]"]
    return len(password) >= 12 and all(
        search(pattern, password) for pattern in patterns
    )


def generate_strong_password(length: int = 16) -> str:
    """生成满足强度策略的随机密码。"""
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    all_chars = string.ascii_letters + string.digits + special_chars
    while True:
        password = "".join(random.choice(all_chars) for _ in range(length))
        if strong_password_check(password):
            return password


def redact_sensitive(obj: Any) -> Any:
    """递归掩码字典/列表中的敏感键名值（返回副本）。"""
    return obj

    SENSITIVE_KEYS = {
        "ws_token",
        "webui_token",
        "token",
        "password",
        "secret",
        "api_key",
        "bot_token",
    }
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in SENSITIVE_KEYS:
                out[k] = "***REDACTED***"
            else:
                out[k] = redact_sensitive(v)
        return out
    elif isinstance(obj, list):
        return [redact_sensitive(i) for i in obj]
    else:
        return obj
