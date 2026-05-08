import asyncio
import json
import time
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

logger = get_logger(__name__)

class VideoStreamer:
    """Manages avatar video streaming to clients."""
    
    def __init__(self, nats_client: NATSClient, duix_renderer, lip_sync_analyzer):
        self.nats = nats_client
        self.renderer = duix_renderer
        self.lip_sync = lip_sync_analyzer
        self.sessions = defaultdict(lambda: {
            "avatar_id": "default",
            "mode": "realtime",
            "emotion": "neutral",
            "enabled": False
        })
        
    async def process_audio_for_avatar(self, msg):
        """Process TTS audio for avatar rendering."""
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())
        
        session = self.sessions[session_id]
        
        if not session["enabled"]:
            return
        
        # Get audio bytes
        audio_hex = data.get("audio", "")
        if not audio_hex:
            return
            
        audio_bytes = bytes.fromhex(audio_hex)
        
        # Analyze lip sync
        visemes = self.lip_sync.analyze(audio_bytes)
        emotion = self.lip_sync.detect_emotion(visemes)
        session["emotion"] = emotion
        
        if session["mode"] == "realtime":
            # Send viseme data to client for browser-side animation
            await self.nats.publish(
                f"session.{session_id}.avatar.visemes",
                {
                    "visemes": visemes,
                    "emotion": emotion
                }
            )
        elif session["mode"] == "hd":
            # Render with Duix
            frame = await self.renderer.render_frame(
                audio_bytes=audio_bytes,
                avatar_id=session["avatar_id"],
                emotion=emotion,
                quality="hd"
            )
            
            if frame:
                await self.nats.publish(
                    f"session.{session_id}.avatar.frame",
                    {"frame": frame.hex(), "timestamp": time.time()}
                )
    
    async def handle_avatar_command(self, msg):
        """Handle avatar control commands."""
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())
        
        session = self.sessions[session_id]
        
        command = data.get("command")
        
        if command == "enable":
            session["enabled"] = True
            session["avatar_id"] = data.get("avatar_id", "default")
            session["mode"] = data.get("mode", "realtime")
            
            # Preload avatar
            await self.renderer.load_avatar(session["avatar_id"])
            
            logger.info(f"Avatar enabled: {session_id} ({session['avatar_id']})")
            
        elif command == "disable":
            session["enabled"] = False
            logger.info(f"Avatar disabled: {session_id}")
            
        elif command == "set_avatar":
            session["avatar_id"] = data.get("avatar_id", "default")
            await self.renderer.load_avatar(session["avatar_id"])
            
        elif command == "set_mode":
            session["mode"] = data.get("mode", "realtime")
            
        elif command == "set_emotion":
            session["emotion"] = data.get("emotion", "neutral")