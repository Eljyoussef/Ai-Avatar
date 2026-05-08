import redis.asyncio as redis
import json
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class HotMemory:
    """Redis-based hot memory for current session state."""
    
    def __init__(self, host: str = "localhost", port: int = 6379):
        self.redis = redis.Redis(host=host, port=port, decode_responses=True)
        
    async def save_conversation(self, session_id: str, messages: List[Dict]):
        """Save recent messages to Redis list."""
        key = f"session:{session_id}:messages"
        
        # Clear old data
        await self.redis.delete(key)
        
        # Save last 20 messages
        for msg in messages[-20:]:
            await self.redis.rpush(key, json.dumps(msg))
        
        # Set TTL
        await self.redis.expire(key, 1800)  # 30 minutes
        
    async def get_conversation(self, session_id: str) -> List[Dict]:
        """Get recent messages from Redis."""
        key = f"session:{session_id}:messages"
        messages = await self.redis.lrange(key, 0, -1)
        return [json.loads(msg) for msg in messages]
    
    async def save_preferences(self, session_id: str, prefs: Dict):
        """Save user preferences."""
        key = f"session:{session_id}:prefs"
        await self.redis.set(key, json.dumps(prefs))
        await self.redis.expire(key, 86400)  # 24 hours
    
    async def get_preferences(self, session_id: str) -> Optional[Dict]:
        """Get user preferences."""
        key = f"session:{session_id}:prefs"
        data = await self.redis.get(key)
        return json.loads(data) if data else None
    
    async def close(self):
        await self.redis.close()