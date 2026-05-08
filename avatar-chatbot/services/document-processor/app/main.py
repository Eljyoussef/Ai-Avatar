import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.logging import get_logger
from .chunking.semantic_chunker import SemanticChunker

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    chunker = SemanticChunker()
    
    async def handle_document_upload(msg):
        data = json.loads(msg.data.decode())
        
        document_text = data.get("text", "")
        metadata = data.get("metadata", {})
        
        chunks = chunker.chunk(document_text, metadata)
        
        logger.info(f"Document chunked: {len(chunks)} chunks")
        
        # Publish chunks for indexing
        await nats_client.publish(
            "document.chunks.ready",
            {
                "chunks": chunks,
                "metadata": metadata
            }
        )
    
    await nats_client.subscribe("document.upload", handle_document_upload)
    
    logger.info("Document Processor running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())