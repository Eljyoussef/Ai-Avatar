import os
from dataclasses import dataclass

@dataclass
class TTSConfig:
    model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    device: str = "cuda"
    sample_rate: int = 24000
    voices_dir: str = "voices"
    
    voice_map: dict = None
    
    def __post_init__(self):
        self.voice_map = {
            "fr-FR-female": os.path.join(self.voices_dir, "fr-fr", "parisian_female.wav"),
            "fr-FR-male": os.path.join(self.voices_dir, "fr-fr", "parisian_male.wav"),
            "fr-CA-female": os.path.join(self.voices_dir, "fr-ca", "quebec_female.wav"),
            "fr-CA-male": os.path.join(self.voices_dir, "fr-ca", "quebec_male.wav"),
            "fr-AF-female": os.path.join(self.voices_dir, "fr-af", "abidjan_female.wav"),
            "fr-AF-male": os.path.join(self.voices_dir, "fr-af", "abidjan_male.wav"),
        }