import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))

from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger
from .config import RAGConfig
from .retrieval.hybrid import HybridRetriever
from .reranking.cross_encoder import CrossEncoderReranker
from .compression.compressor import ContextCompressor

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    
    config = RAGConfig()
    retriever = HybridRetriever(config)
    await retriever.initialize()
    
    reranker = CrossEncoderReranker(config)
    compressor = ContextCompressor()
    
    async def handle_rag_query(msg):
        session_id = msg.subject.split(".")[1]
        data = json.loads(msg.data.decode())
        query = data.get("query", "")
        
        try:
            # Parallel retrieval
            dense_results, sparse_results = await asyncio.gather(
                retriever.dense_search(query, config.dense_top_k),
                retriever.sparse_search(query, config.sparse_top_k)
            )
            
            # Fuse results
            fused = retriever.reciprocal_rank_fusion(dense_results, sparse_results)
            
            # Rerank
            reranked = await reranker.rerank(query, fused)
            top_docs = reranked[:config.final_top_k]
            
            # Compress
            compressed = compressor.compress(query, top_docs)
            
            await nats_client.publish(
                Subjects.rag_results(session_id),
                {
                    "documents": compressed,
                    "query": query,
                    "num_results": len(compressed)
                }
            )
            
            logger.info(f"RAG done: {len(compressed)} docs for '{query[:50]}...'")
            
        except Exception as e:
            logger.error(f"RAG error: {e}")
            await nats_client.publish(
                Subjects.rag_results(session_id),
                {"documents": [], "error": str(e)}
            )
    
    await nats_client.subscribe("session.*.rag.query", handle_rag_query)
    logger.info("RAG Service running")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())