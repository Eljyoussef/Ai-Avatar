import numpy as np
from faster_whisper import WhisperModel
from app.config import ASRConfig
import logging

logger = logging.getLogger(__name__)

class WhisperEngine:
    def __init__(self, config: ASRConfig):
        self.config = config
        self.models = {}
        self.device = config.device
        self.compute_type = config.compute_type

    async def load_models(self):
        """Load whisper models for each accent."""
        for accent, model_name in self.config.accent_models.items():
            try:
                self.models[accent] = WhisperModel(
                    model_name,
                    device=self.device,
                    compute_type=self.compute_type,
                    num_workers=4
                )
                logger.info(f"Loaded Whisper model for {accent}: {model_name}")
            except Exception as e:
                logger.error(f"Failed to load {accent} model: {e}")
                # Fallback to multilingual if available
                if "multilingual" in self.models:
                    self.models[accent] = self.models["multilingual"]

    async def transcribe(self, audio_bytes: bytes, accent: str) -> str:
        """Transcribe audio with accent-specific model."""
        model = self.models.get(accent, self.models.get("multilingual"))
        
        if not model:
            return ""
            
        # Convert bytes to numpy float32 array
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        segments, _ = model.transcribe(
            audio,
            beam_size=self.config.beam_size,
            language=self.config.language,
            vad_filter=True,
            vad_parameters=dict(
                min_silence_duration_ms=500,
                speech_pad_ms=400
            )
        )
        
        text = " ".join(segment.text for segment in segments)
        return text.strip()