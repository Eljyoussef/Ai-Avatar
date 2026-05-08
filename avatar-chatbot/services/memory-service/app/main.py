import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger
from .redis_store.hot_memory import HotMemory
from .postgres_store.persistent import PersistentMemory
from .semantic_memory.qdrant_store import SemanticMemory

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    hot_memory = HotMemory()
    persistent = PersistentMemory(
        dsn=f"postgresql://{os.getenv('POSTGRES_USER', 'chatbot')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'chatbot_secret')}@"
            f"{os.getenv('POSTGRES_HOST', 'localhost')}/"
            f"{os.getenv('POSTGRES_DB', 'chatbot')}"
    )
    await persistent.initialize()
    
    semantic = SemanticMemory()
    await semantic.initialize()
    
    async def handle_memory_update(msg):
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())
        
        # Save to hot memory (Redis)
        # Hot memory is handled by session-manager
        
        # Save to persistent memory
        await persistent.save_message(
            conversation_id=session_id,
            role=data.get("role", "user"),
            content=data.get("content", ""),
            documents_used=data.get("documents_used"),
            latency_ms=data.get("latency_ms")
        )
        
        logger.debug(f"Memory saved: {session_id}")
    
    await nats_client.subscribe("session.*.memory.update", handle_memory_update)
    
    logger.info("Memory Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())