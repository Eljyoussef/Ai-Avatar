import os
from dataclasses import dataclass

@dataclass
class InferenceConfig:
    vllm_base_url: str = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    vllm_model: str = os.getenv("VLLM_MODEL", "mistralai/Mistral-7B-Instruct-v0.3")
    max_tokens: int = 1024
    temperature: float = 0.7
    streaming: bool = True
    
    # Fallback model (local, smaller)
    fallback_model: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"