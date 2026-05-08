import httpx
import json
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

class DuixRenderer:
    """Integration with Duix avatar rendering engine."""
    
    def __init__(self, config):
        self.config = config
        self.api_url = config.duix_api_url
        self.avatar_cache: Dict[str, dict] = {}
        
    async def check_health(self) -> bool:
        """Check if Duix service is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.api_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    async def render_frame(
        self,
        audio_bytes: bytes,
        avatar_id: str,
        emotion: str = "neutral",
        quality: str = "realtime"
    ) -> Optional[bytes]:
        """Render a single frame with audio for lip sync."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_url}/render",
                    files={"audio": audio_bytes},
                    data={
                        "avatar_id": avatar_id,
                        "emotion": emotion,
                        "quality": quality,
                        "lip_sync": str(self.config.lip_sync_enabled).lower()
                    }
                )
                
                if response.status_code == 200:
                    return response.content
                else:
                    logger.error(f"Render failed: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Render error: {e}")
            return None
    
    async def load_avatar(self, avatar_id: str) -> Dict:
        """Load avatar model into memory."""
        if avatar_id in self.avatar_cache:
            return self.avatar_cache[avatar_id]
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.post(
                    f"{self.api_url}/avatar/load",
                    json={"avatar_id": avatar_id}
                )
                
                if response.status_code == 200:
                    avatar_data = response.json()
                    
                    # Cache management
                    if len(self.avatar_cache) >= self.config.max_cache_size:
                        oldest = next(iter(self.avatar_cache))
                        del self.avatar_cache[oldest]
                    
                    self.avatar_cache[avatar_id] = avatar_data
                    return avatar_data
                    
        except Exception as e:
            logger.error(f"Avatar load error: {e}")
        
        return {"avatar_id": avatar_id, "status": "unknown"}
    
    async def get_emotions(self) -> list:
        """Get list of supported emotions."""
        return ["neutral", "happy", "sad", "surprised", "thoughtful", "concerned"]