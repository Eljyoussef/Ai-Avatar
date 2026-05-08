import webrtcvad
import numpy as np

class VoiceActivityDetector:
    def __init__(self, config):
        self.vad = webrtcvad.Vad(config.vad_mode)
        self.sample_rate = 16000
        self.frame_duration = 30  # ms
        self.frame_size = int(self.sample_rate * self.frame_duration / 1000)
        self.silence_threshold = config.silence_threshold
        
    def is_speech(self, audio_array: np.ndarray) -> bool:
        """Detect if audio frame contains speech."""
        if len(audio_array) < self.frame_size:
            return False
            
        # Convert to 16-bit PCM
        audio_int16 = (audio_array * 32768).astype(np.int16)
        
        # Process in 30ms frames
        speech_frames = 0
        total_frames = 0
        
        for i in range(0, len(audio_int16) - self.frame_size, self.frame_size):
            frame = audio_int16[i:i + self.frame_size]
            try:
                if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                    speech_frames += 1
                total_frames += 1
            except:
                continue
        
        if total_frames == 0:
            return False
            
        speech_ratio = speech_frames / total_frames
        return speech_ratio > 0.3