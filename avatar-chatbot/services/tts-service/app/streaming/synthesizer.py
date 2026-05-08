import asyncio
import json
from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger

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
                try: