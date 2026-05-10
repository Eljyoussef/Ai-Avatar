import asyncio, json, sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger
from collections import defaultdict

logger = get_logger(__name__)

class StreamingSynthesizer:
    def __init__(self, tts_engine, nats_client):
        self.tts = tts_engine
        self.nats = nats_client
        self.sessions = defaultdict(lambda: {
            "token_buffer": [],
            "voice_id": "fr-FR-female",
            "accent": "fr-FR"
        })
        self.phrase_endings = {'.', '!', '?', ':', ';', '\n'}

    async def process_token(self, session_id: str, token: str):
        session = self.sessions[session_id]
        buffer = session["token_buffer"]
        buffer.append(token)
        if token in self.phrase_endings or len(buffer) > 20:
            phrase = ''.join(buffer).strip()
            if phrase:
                await self.nats.publish(
                    f"session.{session_id}.audio.output",
                    {"audio": "test", "text": phrase}
                )
                await self.nats.publish(
                    f"session.{session_id}.output",
                    {"type": "audio_chunk", "text": phrase}
                )
                logger.debug(f"TTS: {phrase[:50]}...")
            buffer.clear()

async def main():
    nc = NATSClient()
    await nc.connect()
    synth = StreamingSynthesizer(None, nc)
    async def handle_token(msg):
        sid = msg.subject.split(".")[1]
        data = json.loads(msg.data.decode())
        await synth.process_token(sid, data.get("token", ""))
    await nc.subscribe("session.*.llm.token", handle_token)
    logger.info("TTS Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())