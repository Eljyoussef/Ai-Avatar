import asyncpg
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class PersistentMemory:
    """PostgreSQL-based persistent memory."""
    
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.pool = None
        
    async def initialize(self):
        self.pool = await asyncpg.create_pool(self.dsn)
        logger.info("PostgreSQL pool created")
        
    async def save_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        # documents_used: List[str] = None,
        latency_ms: int = None
    ):
        """Save a message to PostgreSQL."""
        async with self.pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO messages (conversation_id, role, content, latency_ms)
                VALUES ($1, $2, $3, $4, $5)
                """,
                conversation_id, role, content, latency_ms
            )
    
    async def get_conversation_history(
        self, 
        conversation_id: str, 
        limit: int = 50
    ) -> List[Dict]:
        """Get conversation history."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT role, content, created_at
                FROM messages
                WHERE conversation_id = $1
                ORDER BY created_at DESC
                LIMIT $2
                """,
                conversation_id, limit
            )
            
            return [
                {
                    "role": row["role"],
                    "content": row["content"],
                    "timestamp": row["created_at"].isoformat()
                }
                for row in reversed(rows)
            ]
    
    async def create_conversation(self, user_id: str, session_id: str) -> str:
        """Create a new conversation record."""
        async with self.pool.acquire() as conn:
            conv_id = await conn.fetchval(
                """
                INSERT INTO conversations (user_id, session_id)
                VALUES ($1, $2)
                RETURNING id::text
                """,
                user_id, session_id
            )
            return conv_id
    
    async def close(self):
        if self.pool:
            await self.pool.close()