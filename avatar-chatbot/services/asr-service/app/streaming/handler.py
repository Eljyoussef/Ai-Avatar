import asyncio
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger
from ..whisper.engine import WhisperEngine
from ..vad.detector import VoiceActivityDetector
from ..config import ASRConfig

logger = get_logger(__name__)

class StreamingASRHandler:
    def __init__(self, config: ASRConfig, nats_client: NATSClient):
        self.config = config
        self.nats = nats_client
        self.whisper = WhisperEngine(config)
        self.vad = VoiceActivityDetector(config)
        self.sessions = {}

    async def initialize(self):
        await self.whisper.load_models()
        await self.nats.subscribe("session.*.audio.input", self._handle_audio)
        logger.info("ASR Handler ready")

    async def _handle_audio(self, msg):
        subject = msg.subject
        session_id = subject.split(".")[1]
        audio_data = msg.data

        if session_id not in self.sessions:
            self.sessions[session_id] = {
                "audio_buffer": bytearray(),
                "last_speech": time.time(),
                "is_speaking": False,
                "accent": "fr-FR"
            }

        session = self.sessions[session_id]
        session["audio_buffer"].extend(audio_data)

        import numpy as np
        audio_array = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        is_speech = self.vad.is_speech(audio_array)

        if is_speech:
            session["last_speech"] = time.time()
            if not session["is_speaking"]:
                session["is_speaking"] = True

            partial_text = await self.whisper.transcribe(
                bytes(session["audio_buffer"]),
                session["accent"]
            )

            await self.nats.publish(
                Subjects.asr_partial(session_id),
                {"text": partial_text, "is_partial": True, "timestamp": time.time()}
            )
        else:
            if session["is_speaking"]:
                silence = time.time() - session["last_speech"]
                if silence > self.config.silence_threshold:
                    final_text = await self.whisper.transcribe(
                        bytes(session["audio_buffer"]),
                        session["accent"]
                    )

                    await self.nats.publish(
                        Subjects.asr_final(session_id),
                        {"text": final_text, "is_partial": False, "timestamp": time.time()}
                    )

                    session["audio_buffer"] = bytearray()
                    session["is_speaking"] = False
                    logger.info(f"ASR final [{session_id}]: {final_text[:100]}...")

    async def shutdown(self):
        self.sessions.clear()
        logger.info("ASR Handler shutdown")