import os
from dataclasses import dataclass

@dataclass
class ASRConfig:
    model_size: str = os.getenv("WHISPER_MODEL", "large-v3")
    device: str = "cuda"
    compute_type: str = "float16"
    language: str = "fr"
    beam_size: int = 5
    vad_mode: int = 3  # Aggressive VAD
    silence_threshold: float = 0.5  # seconds
    max_buffer_seconds: int = 10
    
    # Accent-specific model paths
    accent_models: dict = None
    
    def __post_init__(self):
        self.accent_models = {
            "fr-FR": os.getenv("WHISPER_FR_MODEL", self.model_size),
            "fr-CA": os.getenv("WHISPER_CA_MODEL", self.model_size),
            "fr-AF": os.getenv("WHISPER_AF_MODEL", self.model_size),
            "fr-BE": os.getenv("WHISPER_BE_MODEL", self.model_size),
            "fr-CH": os.getenv("WHISPER_CH_MODEL", self.model_size),
            "multilingual": self.model_size,
        }