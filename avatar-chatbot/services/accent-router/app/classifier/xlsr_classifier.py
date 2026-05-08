import torch
import torch.nn as nn
import numpy as np
from transformers import Wav2Vec2ForSequenceClassification, Wav2Vec2FeatureExtractor
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

class AccentClassifier:
    """XLS-R based accent classifier for French variants."""
    
    def __init__(self, config):
        self.config = config
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.feature_extractor = None
        self.labels = config.supported_accents
        
    async def load_model(self):
        """Load the accent classification model."""
        try:
            self.feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
                self.config.model_name
            )
            self.model = Wav2Vec2ForSequenceClassification.from_pretrained(
                self.config.model_name,
                num_labels=len(self.labels),
                ignore_mismatched_sizes=True
            ).to(self.device)
            self.model.eval()
            logger.info(f"Accent classifier loaded on {self.device}")
        except Exception as e:
            logger.error(f"Failed to load accent model: {e}")
            # Will use fallback classification
            self.model = None
    
    async def classify(self, audio_data: bytes) -> Tuple[str, float]:
        """
        Classify audio accent.
        Returns (accent_code, confidence).
        """
        if self.model is None:
            return self.config.default_accent, 0.0
        
        try:
            # Convert bytes to numpy array
            audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            
            # Check minimum duration
            duration = len(audio) / self.config.sample_rate
            if duration < self.config.min_audio_duration:
                return self.config.default_accent, 0.0
            
            # Feature extraction
            inputs = self.feature_extractor(
                audio,
                sampling_rate=self.config.sample_rate,
                return_tensors="pt",
                padding=True
            )
            
            # Move to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Inference
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probabilities = torch.nn.functional.softmax(logits, dim=-1)
                
            # Get best prediction
            max_prob, max_idx = torch.max(probabilities[0], dim=0)
            confidence = max_prob.item()
            
            if confidence >= self.config.confidence_threshold:
                accent = self.labels[max_idx.item()]
            else:
                accent = self.config.default_accent
            
            return accent, confidence
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return self.config.default_accent, 0.0
    
    def classify_quick(self, audio_data: bytes) -> str:
        """Quick classification using acoustic features (fallback)."""
        audio = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        
        if len(audio) < 1000:
            return self.config.default_accent
        
        # Simple heuristic based on spectral features
        # This is a lightweight fallback when the model fails
        
        # Calculate spectral centroid (brightness)
        from numpy.fft import rfft
        spectrum = np.abs(rfft(audio[:16000]))  # First second
        freqs = np.fft.rfftfreq(len(audio[:16000]), 1/16000)
        
        if len(spectrum) == 0:
            return self.config.default_accent
            
        centroid = np.sum(freqs * spectrum) / np.sum(spectrum)
        
        # Rough mapping based on spectral centroid
        if centroid > 2000:
            return "fr-CA"  # Quebec tends to have higher spectral centroid
        elif centroid > 1500:
            return "fr-AF"  # African French
        elif centroid > 1000:
            return "fr-FR"
        else:
            return "fr-BE"  # Belgian/Swiss tend lower