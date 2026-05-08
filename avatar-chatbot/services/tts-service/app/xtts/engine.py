import torch
from TTS.api import TTS
import numpy as np
from ..config import TTSConfig
import logging

logger = logging.getLogger(__name__)

class XTTSEngine:
    def __init__(self, config: TTSConfig):
        self.config = config
        self.device = config.device
        self.tts = None
        self.voices = {}

    async def load_voices(self):
        """Load TTS model and voices."""
        self.tts = TTS(self.config.model_name)
        self.tts.to(self.device)

        for voice_id, speaker_path in self.config.voice_map.items():
            if os.path.exists(speaker_path):
                self.voices[voice_id] = speaker_path
        
        logger.info(f"Loaded {len(self.voices)} voices")

    def synthesize(self, text: str, voice_id: str, speed: float = 1.0) -> bytes:
        """Convert text to speech audio bytes."""
        speaker_wav = self.voices.get(voice_id)
        if not speaker_wav:
            speaker_wav = list(self.voices.values())[0] if self.voices else None
            if not speaker_wav:
                raise ValueError("No voices available")

        wav = self.tts.tts(
            text=text,
            speaker_wav=speaker_wav,
            language="fr",
            speed=speed
        )

        wav_array = np.array(wav, dtype=np.float32)
        wav_int16 = (wav_array * 32767).astype(np.int16)
        return wav_int16.tobytes()