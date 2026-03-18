"""Bilibili 扫码登录模块

通过 bilibili_api.login_v2.QrCodeLogin 实现终端扫码获取凭据。
在终端打印 ASCII 二维码，同时保存 PNG 图片供手机扫描。
"""

from __future__ import annotations

import asyncio
import os
import tempfile
from typing import TYPE_CHECKING

from ncatbot.utils import get_log

if TYPE_CHECKING:
    from bilibili_api import Credential

LOG = get_log("BilibiliAuth")

# 二维码约 3 分钟过期，每 2 秒轮询一次状态
_POLL_INTERVAL = 2.0
_MAX_RETRIES = 3  # 过期后最多重新生成 3 次


async def qrcode_login() -> "Credential":
    """交互式扫码登录，返回包含有效凭据的 Credential 对象。

    流程：
    1. 生成二维码（终端 ASCII + PNG 文件）
    2. 轮询登录状态，直到用户扫码确认
    3. 二维码过期自动重新生成（最多 ``_MAX_RETRIES`` 次）

    Raises:
        RuntimeError: 超过最大重试次数仍未完成登录。
    """
    from bilibili_api.login_v2 import (
        QrCodeLogin,
        QrCodeLoginChannel,
        QrCodeLoginEvents,
    )

    for attempt in range(1, _MAX_RETRIES + 1):
        qr = QrCodeLogin(QrCodeLoginChannel.WEB)
        await qr.generate_qrcode()

        # 保存 PNG 到临时文件
        png_path = os.path.join(tempfile.gettempdir(), "ncatbot_bilibili_qr.png")
        pic = qr.get_qrcode_picture()
        if pic is not None and pic.content:
            with open(png_path, "wb") as f:
                f.write(pic.content)
            LOG.info("二维码图片已保存: %s", png_path)

        # 终端 ASCII 打印
        terminal_str = qr.get_qrcode_terminal()
        print("\n" + "=" * 50)
        print(f"  Bilibili 扫码登录 (第 {attempt}/{_MAX_RETRIES} 次)")
        print("=" * 50)
        print(terminal_str)
        print(f"  二维码图片: {png_path}")
        print("  请使用 Bilibili APP 扫描上方二维码")
        print("=" * 50 + "\n")

        # 轮询状态
        while True:
            await asyncio.sleep(_POLL_INTERVAL)
            state = await qr.check_state()

            if state == QrCodeLoginEvents.DONE:
                LOG.info("Bilibili 扫码登录成功")
                return qr.get_credential()
            elif state == QrCodeLoginEvents.CONF:
                LOG.info("已扫码，等待确认...")
            elif state == QrCodeLoginEvents.TIMEOUT:
                LOG.warning("二维码已过期")
                break  # 跳出内层循环，重新生成
            # SCAN 状态 → 继续等待

    raise RuntimeError(f"Bilibili 扫码登录失败: 已超过最大重试次数 ({_MAX_RETRIES})")
