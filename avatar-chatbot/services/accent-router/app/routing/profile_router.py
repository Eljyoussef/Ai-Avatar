from typing import Dict, Optional
from ..profiles.accent_profiles import ACCENT_PROFILES, AccentProfile
import logging

logger = logging.getLogger(__name__)

class ProfileRouter:
    """Routes to appropriate accent profiles based on classification."""
    
    def __init__(self, config):
        self.config = config
        self.profiles = ACCENT_PROFILES
        self.default_profile = self.profiles.get(config.default_accent)
        
    def get_profile(self, accent_code: str) -> AccentProfile:
        """Get the accent profile for a given code."""
        profile = self.profiles.get(accent_code)
        if profile is None:
            logger.warning(f"Unknown accent: {accent_code}, using default")
            profile = self.default_profile
        return profile
    
    def get_asr_model(self, accent_code: str) -> str:
        """Get the ASR model for an accent."""
        return self.get_profile(accent_code).asr_model
    
    def get_tts_voice(self, accent_code: str, gender: str = "female") -> str:
        """Get the TTS voice ID for an accent and gender."""
        profile = self.get_profile(accent_code)
        if gender == "male":
            return profile.tts_voice_male
        return profile.tts_voice_female
    
    def get_vocabulary_bias(self, accent_code: str) -> list:
        """Get vocabulary bias list for ASR."""
        return self.get_profile(accent_code).vocabulary_bias
    
    def get_pronunciation_rules(self, accent_code: str) -> dict:
        """Get pronunciation rules for TTS."""
        return self.get_profile(accent_code).pronunciation_rules
    
    def get_all_accents(self) -> list:
        """Get list of all supported accents."""
        return [
            {
                "code": p.code,
                "name": p.name,
                "region": p.region
            }
            for p in self.profiles.values()
        ]