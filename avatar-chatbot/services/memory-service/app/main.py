import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger

logger = get_logger(__name__)

async def connect_qdrant_with_retry(max_retries=10):
    """Try to connect to Qdrant with retries."""
    from qdrant_client import QdrantClient
    
    host = os.getenv('QDRANT_HOST', 'qdrant')
    port = int(os.getenv('QDRANT_PORT', '6333'))
    
    for attempt in range(max_retries):
        try:
            client = QdrantClient(host=host, port=port)
            collections = client.get_collections()
            logger.info(f"Qdrant connected on attempt {attempt + 1}")
            return client
        except Exception as e:
            logger.warning(f"Qdrant attempt {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(3)
    
    logger.error("Failed to connect to Qdrant after all retries")
    return None

async def main():
    nats_client = NATSClient()
    await nats_client.connect()

    # Try to connect to services
    qdrant_client = await connect_qdrant_with_retry()
    
    # Try Redis
    try:
        from .redis_store.hot_memory import HotMemory
        hot_memory = HotMemory(
            host=os.getenv('REDIS_HOST', 'redis'),
            port=int(os.getenv('REDIS_PORT', '6379'))
        )
        logger.info("Redis connected")
    except Exception as e:
        logger.warning(f"Redis not available: {e}")
        hot_memory = None

    # Try PostgreSQL
    try:
        from .postgres_store.persistent import PersistentMemory
        persistent = PersistentMemory(
            dsn=f"postgresql://{os.getenv('POSTGRES_USER', 'chatbot')}:"
                f"{os.getenv('POSTGRES_PASSWORD', 'chatbot_secret')}@"
                f"{os.getenv('POSTGRES_HOST', 'postgres')}/"
                f"{os.getenv('POSTGRES_DB', 'chatbot')}"
        )
        await persistent.initialize()
        logger.info("PostgreSQL connected")
    except Exception as e:
        logger.warning(f"PostgreSQL not available: {e}")
        persistent = None

    # Try Semantic Memory
    semantic = None
    if qdrant_client:
        try:
            from .semantic_memory.qdrant_store import SemanticMemory
            semantic = SemanticMemory(
                host=os.getenv('QDRANT_HOST', 'qdrant'),
                port=int(os.getenv('QDRANT_PORT', '6333'))
            )
            await semantic.initialize()
            logger.info("Semantic memory ready")
        except Exception as e:
            logger.warning(f"Semantic memory not available: {e}")

    async def handle_memory_update(msg):
        subject = msg.subject
        session_id = subject.split(".")[1]
        data = json.loads(msg.data.decode())

        # Save to persistent memory if available
        if persistent:
            try:
                await persistent.save_message(
                    conversation_id=session_id,
                    role=data.get("role", "user"),
                    content=data.get("content", ""),
                    documents_used=data.get("documents_used"),
                    latency_ms=data.get("latency_ms")
                )
                logger.debug(f"Memory saved to PostgreSQL: {session_id}")
            except Exception as e:
                logger.error(f"PostgreSQL save error: {e}")

        # Save to semantic memory if available
        if semantic and data.get("role") == "user":
            try:
                await semantic.store_fact(
                    user_id=data.get("user_id", session_id),
                    fact=data.get("content", ""),
                    metadata={"session_id": session_id}
                )
            except Exception as e:
                logger.error(f"Semantic save error: {e}")

    await nats_client.subscribe("session.*.memory.update", handle_memory_update)

    logger.info("Memory Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())