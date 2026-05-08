import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from ..main import nats_client
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, WebSocket] = {}

    async def connect(self, session_id: str, ws: WebSocket):
        await ws.accept()
        self.connections[session_id] = ws
        logger.info(f"Connected: {session_id}")

    def disconnect(self, session_id: str):
        self.connections.pop(session_id, None)

    async def send(self, session_id: str, data: dict):
        if session_id in self.connections:
            await self.connections[session_id].send_json(data)

manager = ConnectionManager()

@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(session_id, websocket)

    # Listen for NATS messages to this session
    async def forward_to_client(msg):
        data = json.loads(msg.data.decode())
        await manager.send(session_id, data)

    sub = await nats_client.subscribe(
        Subjects.session_output(session_id), 
        forward_to_client
    )

    try:
        while True:
            data = await websocket.receive()

            if "text" in data:
                msg = json.loads(data["text"])
                msg_type = msg.get("type")

                if msg_type == "chat":
                    await nats_client.publish(
                        Subjects.asr_final(session_id),
                        {"text": msg["content"], "source": "text"}
                    )
                elif msg_type == "interrupt":
                    await nats_client.publish(
                        Subjects.control_interrupt(session_id),
                        {}
                    )

            elif "bytes" in data:
                await nats_client.publish(
                    Subjects.audio_input(session_id),
                    data["bytes"]
                )

    except WebSocketDisconnect:
        logger.info(f"Disconnected: {session_id}")
    finally:
        await sub.unsubscribe()
        manager.disconnect(session_id)