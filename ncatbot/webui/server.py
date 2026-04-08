"""WebUI aiohttp server — WebSocket message routing"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import aiohttp
from aiohttp import web

from .protocol import MsgType, make_response
from .recorder import RecordingEngine
from .session import SessionManager

logger = logging.getLogger(__name__)


def create_app(session_mgr: Optional[SessionManager] = None) -> web.Application:
    """Create aiohttp Application with WebSocket endpoint."""
    app = web.Application()
    if session_mgr is None:
        session_mgr = SessionManager()
    app["session_mgr"] = session_mgr

    app.router.add_get("/ws", ws_handler)
    return app


async def ws_handler(request: web.Request) -> web.WebSocketResponse:
    """WebSocket message router."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    session_mgr: SessionManager = request.app["session_mgr"]
    recorders: dict[str, RecordingEngine] = {}

    async for raw_msg in ws:
        if raw_msg.type == aiohttp.WSMsgType.TEXT:
            try:
                data = json.loads(raw_msg.data)
            except json.JSONDecodeError:
                await ws.send_json(
                    make_response(MsgType.ERROR, {"message": "Invalid JSON"})
                )
                continue

            msg_type = data.get("type", "")
            payload = data.get("payload", {})
            msg_id = data.get("id")

            try:
                await _route_message(
                    ws, session_mgr, recorders, msg_type, payload, msg_id
                )
            except KeyError as exc:
                await ws.send_json(
                    make_response(
                        MsgType.ERROR,
                        {"message": f"Unknown session or event type: {exc}"},
                        msg_id,
                    )
                )
            except Exception as exc:
                logger.exception("WebSocket handler error")
                await ws.send_json(
                    make_response(
                        MsgType.ERROR,
                        {"message": str(exc)},
                        msg_id,
                    )
                )
        elif raw_msg.type == aiohttp.WSMsgType.ERROR:
            logger.error("WebSocket error: %s", ws.exception())

    # Cleanup sessions owned by this WS connection
    for sid in list(recorders):
        try:
            await session_mgr.destroy_session(sid)
        except KeyError:
            pass

    return ws


async def _route_message(
    ws: web.WebSocketResponse,
    session_mgr: SessionManager,
    recorders: dict[str, RecordingEngine],
    msg_type: str,
    payload: dict,
    msg_id: Optional[str],
):
    if msg_type == MsgType.SESSION_CREATE:
        session_id = await session_mgr.create_session(
            platform=payload.get("platform", "qq"),
            plugins=payload.get("plugins"),
        )
        proxy = session_mgr.get(session_id)
        recorders[session_id] = RecordingEngine()

        # Register real-time API call push
        def on_api_call(action, params, sid=session_id):
            asyncio.ensure_future(
                ws.send_json(
                    make_response(
                        MsgType.API_CALLED,
                        {
                            "session_id": sid,
                            "action": action,
                            "params": _serialize_params(params),
                        },
                    )
                )
            )

        proxy.on_api_call(on_api_call)

        await ws.send_json(
            make_response(
                MsgType.SESSION_CREATED,
                {
                    "session_id": session_id,
                    "platform": payload.get("platform", "qq"),
                },
                msg_id,
            )
        )

    elif msg_type == MsgType.EVENT_INJECT:
        session_id = payload["session_id"]
        proxy = session_mgr.get(session_id)
        recorder = recorders.get(session_id)

        await proxy.inject(payload["event_type"], payload["data"])
        if recorder:
            recorder.record_inject(payload["event_type"], payload["data"])

    elif msg_type == MsgType.EVENT_INJECT_RAW:
        session_id = payload["session_id"]
        proxy = session_mgr.get(session_id)
        await proxy.inject_raw(payload["raw"])

    elif msg_type == MsgType.SESSION_SETTLE:
        session_id = payload["session_id"]
        proxy = session_mgr.get(session_id)
        recorder = recorders.get(session_id)

        calls = await proxy.settle()
        if recorder:
            recorder.record_settle(calls)

        await ws.send_json(
            make_response(
                MsgType.SETTLE_DONE,
                {"session_id": session_id, "api_calls": calls},
                msg_id,
            )
        )

    elif msg_type == MsgType.RECORDING_START:
        session_id = payload["session_id"]
        recorder = recorders.get(session_id)
        if recorder:
            recorder.start()

    elif msg_type == MsgType.RECORDING_STOP:
        session_id = payload["session_id"]
        recorder = recorders.get(session_id)
        if recorder:
            recorder.stop()

    elif msg_type == MsgType.RECORDING_EXPORT:
        session_id = payload["session_id"]
        recorder = recorders.get(session_id)
        code = recorder.export_scenario_dsl() if recorder else ""
        await ws.send_json(
            make_response(
                MsgType.RECORDING_EXPORTED,
                {"session_id": session_id, "code": code},
                msg_id,
            )
        )

    elif msg_type == MsgType.SESSION_DESTROY:
        session_id = payload["session_id"]
        await session_mgr.destroy_session(session_id)
        recorders.pop(session_id, None)

    else:
        await ws.send_json(
            make_response(
                MsgType.ERROR,
                {"message": f"Unknown message type: {msg_type}"},
                msg_id,
            )
        )


def _serialize_params(params: dict) -> dict:
    """Best-effort JSON serialization of API call params."""
    result = {}
    for k, v in params.items():
        try:
            json.dumps(v)
            result[k] = v
        except (TypeError, ValueError):
            result[k] = str(v)
    return result


async def start_webui(
    port: int = 8765,
    plugins: list[str] | None = None,
    dev: bool = False,
):
    """Start the WebUI server (blocking)."""
    app = create_app()

    if not dev:
        static_dir = Path(__file__).parent / "static"
        if static_dir.exists():
            app.router.add_static("/assets", static_dir / "assets")

            async def serve_index(request: web.Request) -> web.FileResponse:
                return web.FileResponse(static_dir / "index.html")

            # Catch-all for SPA routing — must be added LAST
            app.router.add_get("/{path:.*}", serve_index)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", port)
    await site.start()
    print(f"NcatBot TestUI: http://localhost:{port}")

    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
