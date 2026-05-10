import asyncio
import json
import sys
import os
from typing import Dict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from shared.logging import get_logger

logger = get_logger(__name__)

try:
    from shared.nats.client import NATSClient
    HAS_NATS = True
except:
    HAS_NATS = False

try:
    from .config import AvatarConfig
    from .duix.renderer import DuixRenderer
    from .synchronization.lip_sync import LipSyncAnalyzer
    from .streaming.video_streamer import VideoStreamer
    HAS_AVATAR = True
except Exception as e:
    logger.warning(f"Avatar modules not available: {e}")
    HAS_AVATAR = False


async def main():
    if HAS_NATS and HAS_AVATAR:
        nats_client = NATSClient()
        await nats_client.connect()
        
        config = AvatarConfig()
        renderer = DuixRenderer(config)
        lip_sync = LipSyncAnalyzer()
        video_streamer = VideoStreamer(nats_client, renderer, lip_sync)
        
        duix_available = await renderer.check_health()
        logger.info(f"Duix available: {duix_available}")
        
        await nats_client.subscribe("session.*.avatar.render", video_streamer.process_audio_for_avatar)
        await nats_client.subscribe("session.*.avatar.command", video_streamer.handle_avatar_command)
        
        await nats_client.publish("avatar.ready", {
            "duix_available": duix_available,
            "modes": ["realtime", "hd"]
        })
    
    logger.info(f"Avatar Adapter running — NATS:{HAS_NATS} Avatar:{HAS_AVATAR}")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())