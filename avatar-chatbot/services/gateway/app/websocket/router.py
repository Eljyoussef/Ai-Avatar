import json, asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.main import nats_client
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[session_id] = ws

    def disconnect(self, session_id: str):
        self._connections.pop(session_id, None)

    async def send_json(self, session_id: str, data: dict):
        ws = self._connections.get(session_id)
        if ws:
            await ws.send_json(data)

    async def send_bytes(self, session_id: str, data: bytes):
        ws = self._connections.get(session_id)
        if ws:
            await ws.send_bytes(data)


manager = ConnectionManager()


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)
    await websocket.send_json({"type": "connected", "session_id": session_id})

    async def forward_output(msg):
        try:
            payload = json.loads(msg.data.decode())
            await manager.send_json(session_id, payload)
        except Exception:
            pass

    sub_output = await nats_client.subscribe(Subjects.session_output(session_id), forward_output)

    # Forward audio separately (binary)
    async def forward_audio(msg):
        await manager.send_bytes(session_id, msg.data)

    sub_audio = await nats_client.subscribe(Subjects.audio_output(session_id), forward_audio)

    try:
        while True:
            raw = await websocket.receive()

            if "text" in raw:
                msg = json.loads(raw["text"])
                msg_type = msg.get("type", "")

                if msg_type == "chat":
                    content = msg.get("content", "").strip()
                    if not content:
                        continue
                    await nats_client.publish(Subjects.asr_final(session_id), {
                        "text": content, "source": "text", "is_partial": False,
                        "accent": msg.get("accent", "fr-FR"),
                        "gender": msg.get("gender", "neutral"),
                    })

                elif msg_type == "interrupt":
                    await nats_client.publish(Subjects.interrupt(session_id), {})

                elif msg_type == "accent_change":
                    await nats_client.publish(f"session.{session_id}.accent.update", {"accent": msg.get("accent")})

                elif msg_type == "gender_change":
                    await nats_client.publish(f"session.{session_id}.gender.update", {"gender": msg.get("gender")})

            elif "bytes" in raw:
                await nats_client.publish(Subjects.audio_input(session_id), raw["bytes"])

    except WebSocketDisconnect:
        logger.info(f"WS disconnected: {session_id}")
    finally:
        await sub_output.unsubscribe()
        await sub_audio.unsubscribe()
        manager.disconnect(session_id)