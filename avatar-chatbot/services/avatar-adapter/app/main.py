import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger
from .config import AvatarConfig
from .duix.renderer import DuixRenderer
from .synchronization.lip_sync import LipSyncAnalyzer
from .streaming.video_streamer import VideoStreamer

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    config = AvatarConfig()
    renderer = DuixRenderer(config)
    lip_sync = LipSyncAnalyzer()
    video_streamer = VideoStreamer(nats_client, renderer, lip_sync)
    
    # Check Duix availability
    duix_available = await renderer.check_health()
    if duix_available:
        logger.info("Duix renderer available")
    else:
        logger.warning("Duix renderer not available - using browser-side animations only")
    
    # Subscribe to TTS audio for avatar rendering
    await nats_client.subscribe(
        "session.*.avatar.render",
        video_streamer.process_audio_for_avatar
    )
    
    # Subscribe to avatar commands
    await nats_client.subscribe(
        "session.*.avatar.command",
        video_streamer.handle_avatar_command
    )
    
    # Get supported emotions
    emotions = await renderer.get_emotions()
    
    # Announce availability
    await nats_client.publish(
        "avatar.ready",
        {
            "duix_available": duix_available,
            "supported_emotions": emotions,
            "modes": ["realtime", "hd"]
        }
    )
    
    logger.info("Avatar Adapter running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())