import os
from dataclasses import dataclass, field

@dataclass
class AccentRouterConfig:
    model_name: str = "facebook/wav2vec2-xls-r-300m"
    confidence_threshold: float = 0.7
    sample_rate: int = 16000
    min_audio_duration: float = 2.0  # seconds needed for classification
    
    # Supported accents
    supported_accents: list = field(default_factory=lambda: [
        "fr-FR",  # France métropolitaine
        "fr-CA",  # Québec
        "fr-AF",  # Afrique francophone
        "fr-BE",  # Belgique
        "fr-CH",  # Suisse
        "fr-MG",  # Maghreb
    ])
    
    # Fallback accent when confidence is low
    default_accent: str = "fr-FR"