import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger
from .config import TTSConfig
from .xtts.engine import XTTSEngine
from .streaming.synthesizer import StreamingSynthesizer

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()

    config = TTSConfig()
    engine = XTTSEngine(config)
    await engine.load_voices()

    synthesizer = StreamingSynthesizer(engine, nats_client)

    async def handle_token(msg):
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())
        await synthesizer.process_token(session_id, data["token"])

    # Also handle accent/voice updates
    async def handle_accent_update(msg):
        session_id = msg.subject.split(".")[1]
        data = json.loads(msg.data.decode())
        accent = data.get("accent", "fr-FR")
        gender = data.get("gender", "female")
        synthesizer.sessions[session_id]["accent"] = accent
        synthesizer.sessions[session_id]["voice_id"] = f"{accent}-{gender}"

    await nats_client.subscribe("session.*.llm.token", handle_token)
    await nats_client.subscribe("session.*.accent.update", handle_accent_update)

    logger.info("TTS Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())