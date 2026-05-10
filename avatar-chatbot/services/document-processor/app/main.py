import asyncio, json, sys, os
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
        text = data.get("text", "")
        session_id = data.get("session_id", "default")
        filename = data.get("filename", "unknown")
        
        if not text:
            logger.warning(f"Empty document: {filename}")
            return
        
        chunks = chunker.chunk(text, {"filename": filename, "session_id": session_id})
        logger.info(f"Document chunked: {len(chunks)} chunks from {filename}")
        
        await nats_client.publish("document.chunks.ready", {
            "chunks": chunks,
            "session_id": session_id,
            "filename": filename
        })
    
    await nats_client.subscribe("document.upload", handle_document_upload)
    logger.info("Document Processor running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
