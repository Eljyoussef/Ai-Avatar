import httpx
import json
from typing import AsyncIterator, List, Dict
import logging

logger = logging.getLogger(__name__)

class VLLMProvider:
    def __init__(self, config):
        self.base_url = config.vllm_base_url
        self.model = config.vllm_model
        self.max_tokens = config.max_tokens
        self.temperature = config.temperature
        
    async def generate_stream(
        self, 
        messages: List[Dict],
        session_id: str = None
    ) -> AsyncIterator[str]:
        """Stream tokens from vLLM."""
        
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": True
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload
            ) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        
                        if data == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            
                            if content:
                                yield content
                        except json.JSONDecodeError:
                            continue
    
    async def generate(self, messages: List[Dict]) -> str:
        """Non-streaming generation (fallback)."""
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": False
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            
            return data["choices"][0]["message"]["content"]