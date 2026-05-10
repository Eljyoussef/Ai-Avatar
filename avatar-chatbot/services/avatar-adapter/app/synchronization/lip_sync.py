import numpy as np
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class LipSyncAnalyzer:
    """Analyzes audio for lip sync parameters."""
    
    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        
    def analyze(self, audio_bytes: bytes) -> List[Dict]:
        """Extract lip sync parameters from audio."""
        audio = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        
        if len(audio) == 0:
            return []
        
        # Frame-based analysis
        frame_size = int(self.sample_rate * 0.016)  # 16ms frames
        visemes = []
        
        for i in range(0, len(audio) - frame_size, frame_size):
            frame = audio[i:i + frame_size]
            
            # Calculate features
            energy = np.sqrt(np.mean(frame ** 2))
            zero_crossings = np.sum(np.abs(np.diff(np.sign(frame)))) / (2 * len(frame))
            
            # Map to mouth openness (0-1)
            openness = min(1.0, energy * 10)
            
            # Detect phoneme class
            if energy < 0.01:
                phoneme = "silence"
            elif zero_crossings > 0.3:
                phoneme = "consonant"
            else:
                phoneme = "vowel"
            
            timestamp = i / self.sample_rate
            
            visemes.append({
                "timestamp": timestamp,
                "openness": float(openness),
                "phoneme": phoneme,
                "energy": float(energy)
            })
        
        return visemes
    
    def detect_emotion(self, visemes: List[Dict]) -> str:
        """Detect emotion from speech patterns."""
        if not visemes:
            return "neutral"
        
        energies = [v["energy"] for v in visemes]
        avg_energy = np.mean(energies)
        energy_variance = np.var(energies)
        
        if avg_energy > 0.1 and energy_variance > 0.02:
            return "happy"
        elif avg_energy < 0.02:
            return "sad"
        elif energy_variance > 0.03:
            return "surprised"
        
        return "neutral"