import asyncio
import json
import os
import secrets
import socket
import subprocess
import sys
from pathlib import Path
from urllib import request

from ncatbot.core import registrar
from ncatbot.plugin import BasePlugin


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


class NcatBotJavaBridgePlugin(BasePlugin):
    name = "ncatbot_java_bridge"
    version = "1.0.0"
    author = "NcatBot Java"
    description = "加载并桥接 plugins 目录中的 NcatBot Java Jar 插件"

    def _init_(self):
        self._processes = []
        self._token = secrets.token_urlsafe(24)
        self._api_port = _free_port()
        self._api_server = None
        self._api_runner_task = None
        self._event_targets = []

    async def on_load(self):
        await self._start_api_server()
        await self._start_java_jars()

    async def on_close(self):
        for process in self._processes:
            if process.poll() is None:
                process.terminate()
        for process in self._processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        if self._api_server is not None:
            self._api_server.close()
            await self._api_server.wait_closed()
        if self._api_runner_task is not None:
            self._api_runner_task.cancel()

    async def _start_api_server(self):
        self._api_server = await asyncio.start_server(
            self._handle_api_connection,
            host="127.0.0.1",
            port=self._api_port,
        )
        self._api_runner_task = asyncio.create_task(self._api_server.serve_forever())
        self.logger.info("Java Bridge API 服务已启动: http://127.0.0.1:%s", self._api_port)

    async def _start_java_jars(self):
        plugins_dir = self._manifest.plugin_path.parent if self._manifest else Path("plugins")
        jar_files = [p for p in plugins_dir.iterdir() if p.is_file() and p.suffix.lower() == ".jar"]
        if not jar_files:
            self.logger.info("未发现 Java Jar 插件，请将 jar 放入 plugins 目录")
            return

        for jar_file in jar_files:
            event_port = _free_port()
            work_dir = self.workspace / jar_file.stem
            work_dir.mkdir(parents=True, exist_ok=True)
            command = [
                "java",
                "-jar",
                str(jar_file),
                "--ncatbot-plugin-port",
                str(event_port),
                "--ncatbot-api-url",
                f"http://127.0.0.1:{self._api_port}",
                "--ncatbot-token",
                self._token,
                "--ncatbot-plugin-name",
                jar_file.stem,
                "--ncatbot-work-dir",
                str(work_dir),
            ]
            process = subprocess.Popen(command, cwd=str(plugins_dir))
            self._processes.append(process)
            self._event_targets.append((jar_file.stem, event_port))
            self.logger.info("已启动 Java 插件 %s，事件端口 %s", jar_file.name, event_port)

    async def _handle_api_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            header_bytes = await reader.readuntil(b"\r\n\r\n")
            headers_text = header_bytes.decode("iso-8859-1")
            lines = headers_text.split("\r\n")
            request_line = lines[0]
            method, path, _ = request_line.split(" ", 2)
            headers = {}
            for line in lines[1:]:
                if ":" in line:
                    key, value = line.split(":", 1)
                    headers[key.strip().lower()] = value.strip()
            length = int(headers.get("content-length", "0"))
            body = await reader.readexactly(length) if length > 0 else b"{}"

            auth = headers.get("authorization", "")
            token = headers.get("x-ncatbot-token", "")
            if auth != f"Bearer {self._token}" and token != self._token:
                await self._write_response(writer, 401, {"ok": False, "error": "unauthorized"})
                return
            if method.upper() != "POST" or path != "/api/call":
                await self._write_response(writer, 404, {"ok": False, "error": "not found"})
                return

            payload = json.loads(body.decode("utf-8"))
            action = payload.get("action")
            params = payload.get("params") or {}
            result = await self._call_bot_api(action, params)
            await self._write_response(writer, 200, {"ok": True, "data": result})
        except Exception as exc:
            await self._write_response(writer, 500, {"ok": False, "error": str(exc)})
        finally:
            writer.close()
            await writer.wait_closed()

    async def _write_response(self, writer: asyncio.StreamWriter, status: int, payload: dict):
        reason = "OK" if status == 200 else "ERROR"
        body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
        writer.write(
            f"HTTP/1.1 {status} {reason}\r\nContent-Type: application/json; charset=utf-8\r\nContent-Length: {len(body)}\r\nConnection: close\r\n\r\n".encode("utf-8")
            + body
        )
        await writer.drain()

    async def _call_bot_api(self, action: str, params: dict):
        if not action:
            raise ValueError("缺少 action")
        qq = self.api.qq
        if action in {"send_group_msg", "send_private_msg", "delete_msg"}:
            target = qq.messaging
        elif action.startswith("set_") or action in {"send_group_notice", "delete_group_notice"}:
            target = qq.manage
        elif action.startswith("get_") or action in {"ocr_image", "fetch_emoji_like"}:
            target = qq.query
        elif action in {"upload_group_file", "delete_group_file", "download_file"}:
            target = qq.file
        else:
            target = qq
        method = getattr(target, action)
        return await method(**params)

    async def _dispatch_to_java(self, event):
        if not self._event_targets:
            return
        payload = json.dumps(_event_to_dict(event), ensure_ascii=False, default=str).encode("utf-8")
        for name, port in list(self._event_targets):
            await asyncio.to_thread(self._post_event, name, port, payload)

    def _post_event(self, name: str, port: int, payload: bytes):
        req = request.Request(
            f"http://127.0.0.1:{port}/ncatbot/event",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=10) as resp:
                resp.read()
        except Exception as exc:
            self.logger.warning("转发事件到 Java 插件 %s 失败: %s", name, exc)


@registrar.on("message")
@registrar.on("notice")
@registrar.on("request")
@registrar.on("meta_event")
async def _forward_all_events(self: NcatBotJavaBridgePlugin, event):
    await self._dispatch_to_java(event)


def _event_to_dict(event):
    data = getattr(event, "data", None)
    raw_data = data.model_dump(mode="json") if hasattr(data, "model_dump") else getattr(data, "__dict__", data)
    return {
        "type": getattr(event, "type", ""),
        "platform": getattr(event, "platform", "qq"),
        "data": raw_data,
    }
