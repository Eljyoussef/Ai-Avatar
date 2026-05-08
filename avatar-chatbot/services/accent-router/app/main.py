import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger
from .config import AccentRouterConfig
from .classifier.xlsr_classifier import AccentClassifier
from .routing.profile_router import ProfileRouter

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    config = AccentRouterConfig()
    classifier = AccentClassifier(config)
    router = ProfileRouter(config)
    
    # Try to load the model
    await classifier.load_model()
    
    async def handle_audio_for_accent(msg):
        """Handle incoming audio to classify accent."""
        subject = msg.subject
        session_id = subject.split(".")[1]
        audio_data = msg.data
        
        # Classify accent
        accent, confidence = await classifier.classify(audio_data)
        
        # Get profile
        profile = router.get_profile(accent)
        
        # Publish accent detected
        await nats_client.publish(
            f"session.{session_id}.accent.detected",
            {
                "accent": accent,
                "confidence": confidence,
                "profile_name": profile.name,
                "region": profile.region,
                "asr_model": profile.asr_model,
                "vocabulary_bias": profile.vocabulary_bias
            }
        )
        
        # Update session with accent
        await nats_client.publish(
            f"session.{session_id}.accent.update",
            {
                "accent": accent,
                "tts_voice_female": profile.tts_voice_female,
                "tts_voice_male": profile.tts_voice_male,
                "pronunciation_rules": profile.pronunciation_rules
            }
        )
        
        logger.info(f"Accent [{session_id}]: {accent} ({confidence:.2f})")
    
    async def handle_get_accents(msg):
        """Return list of all supported accents."""
        accents = router.get_all_accents()
        response = json.dumps({"accents": accents}).encode()
        await nats_client.publish(msg.reply, response)
    
    # Subscribe to audio for accent detection
    await nats_client.subscribe("session.*.audio.input", handle_audio_for_accent)
    
    # Subscribe to accent list requests
    await nats_client.subscribe("accent.list", handle_get_accents)
    
    logger.info("Accent Router running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())