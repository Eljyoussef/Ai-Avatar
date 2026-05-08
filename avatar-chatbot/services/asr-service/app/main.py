import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger
from .config import ASRConfig
from .streaming.handler import StreamingASRHandler

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()

    config = ASRConfig()
    handler = StreamingASRHandler(config, nats_client)
    await handler.initialize()

    logger.info("ASR Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())