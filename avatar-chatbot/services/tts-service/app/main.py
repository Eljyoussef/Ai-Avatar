import asyncio, json, sys, os
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)

PUNCTUATION = {'.', '!', '?', ':', ';', '\n'}


async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    buffers: dict[str, list[str]] = defaultdict(list)

    async def on_token(msg):
        sid = msg.subject.split(".")[1]
        data = json.loads(msg.data.decode())
        token = data.get("token", "")
        buf = buffers[sid]
        buf.append(token)

        text = "".join(buf)
        if token and token.strip() and token.strip()[-1] in PUNCTUATION:
            phrase = text.strip()
            if phrase:
                logger.info(f"TTS [{sid}]: {phrase[:60]}")
                # Send as JSON envelope so frontend can handle it
                await nats_client.publish(Subjects.session_output(sid), {
                    "type": "audio_phrase",
                    "text": phrase
                })
            buffers[sid] = []

    await nats_client.subscribe(Subjects.llm_token("*"), on_token)
    logger.info("TTS Service running")
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
