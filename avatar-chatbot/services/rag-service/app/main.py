import asyncio, json, sys, os, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../..'))
from shared.nats.client import NATSClient
from shared.nats.subjects import Subjects
from shared.logging import get_logger
from .config import RAGConfig
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue

logger = get_logger(__name__)

async def main():
    nats_client = NATSClient()
    await nats_client.connect()
    config = RAGConfig()
    
    sessions_with_docs: set = set()
    retriever = None
    pending = []  # ← NEW: queue chunks while retriever loads
    
    async def index_chunks(chunks, session_id, filename):
        points = []
        for chunk in chunks:
            chunk["session_id"] = session_id
            try:
                emb = await asyncio.to_thread(retriever.encoder.encode, chunk["text"])
                emb = emb.tolist()
                points.append(PointStruct(id=str(uuid.uuid4()), vector=emb, payload=chunk))
            except Exception as e:
                logger.error(f"Embed error: {e}")
        if points:
            retriever.qdrant.upsert(collection_name=config.collection_name, points=points, wait=True)
            sessions_with_docs.add(session_id)
            logger.info(f"INDEXED {len(points)} chunks for {session_id} from {filename}")
    
    async def handle_chunks(msg):
        data = json.loads(msg.data.decode())
        chunks = data.get("chunks", [])
        session_id = data.get("session_id", "__global__")
        filename = data.get("filename", "unknown")
        if not chunks:
            return
        if not retriever:
            pending.append((chunks, session_id, filename))
            logger.info(f"QUEUED {len(chunks)} chunks (retriever not ready)")
            return
        await index_chunks(chunks, session_id, filename)
    
    await nats_client.subscribe("document.chunks.ready", handle_chunks)
    logger.info("Listening for chunks...")
    
    for i in range(60):
        try:
            from .retrieval.hybrid import HybridRetriever
            retriever = HybridRetriever(config)
            await retriever.initialize()
            logger.info("RAG retriever ready")
            break
        except Exception as e:
            if i % 15 == 0:
                logger.warning(f"Waiting ({i+1}/60): {str(e)[:80]}")
            await asyncio.sleep(3)
    
    if not retriever:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        class QdrantOnly:
            def __init__(self):
                self.qdrant = QdrantClient(host=config.qdrant_host, port=config.qdrant_port)
                self.encoder = SentenceTransformer(config.embedding_model)
            async def initialize(self): pass
            async def dense_search(self, query, session_id=None, top_k=20):
                vec = await asyncio.to_thread(self.encoder.encode, query)
                vec = vec.tolist()
                kwargs = {"collection_name": config.collection_name, "query": vec, "limit": top_k}
                if session_id:
                    kwargs["query_filter"] = Filter(must=[FieldCondition(key="session_id", match=MatchValue(value=session_id))])
                results = self.qdrant.query_points(**kwargs)
                return [{"id": r.id, "score": r.score, "text": r.payload.get("text",""), "metadata": r.payload.get("metadata",{})} for r in results.points]
            async def sparse_search(self, q, session_id=None, top_k=20): return []
            def reciprocal_rank_fusion(self, d, s, k=60): return d
        retriever = QdrantOnly()
    
    # ← NEW: Index all queued chunks
    for chunks, sid, fn in pending:
        await index_chunks(chunks, sid, fn)
    pending.clear()
    
    reranker = None
    compressor = None
    if retriever:
        try:
            from .reranking.cross_encoder import CrossEncoderReranker
            from .compression.compressor import ContextCompressor
            reranker = CrossEncoderReranker(config)
            compressor = ContextCompressor()
        except Exception as e:
            logger.warning(f"Reranker/compressor not loaded: {e}")
    
    async def handle_rag_query(msg):
        sid = msg.subject.split(".")[1]
        data = json.loads(msg.data.decode())
        query = data.get("query", "")
        gender = data.get("gender", "neutral")
        accent = data.get("accent", "fr-FR")
        mode = data.get("mode", "text")
        has_docs = len(sessions_with_docs) > 0
        logger.info(f"RAG [{sid}]: '{query[:60]}...' has_docs={has_docs} sessions={sessions_with_docs}")
        if not has_docs:
            await nats_client.publish(Subjects.session_output(sid), {
                "type": "text_response",
                "text": "Vous n'avez pas encore telecharge de documents."
            })
            return
        docs = []
        if retriever:
            try:
                dense = await retriever.dense_search(query, top_k=config.dense_top_k)
                sparse = await retriever.sparse_search(query, top_k=config.sparse_top_k)
                fused = retriever.reciprocal_rank_fusion(dense, sparse)
                if fused and reranker and compressor:
                    reranked = await reranker.rerank(query, fused)
                    docs = compressor.compress(query, reranked[:config.final_top_k])
                else:
                    docs = fused[:config.final_top_k] if fused else []
                logger.info(f"RAG found {len(docs)} docs")
            except Exception as e:
                logger.error(f"RAG search error: {e}", exc_info=True)
        if not docs:
            await nats_client.publish(Subjects.session_output(sid), {
                "type": "text_response",
                "text": "Aucune information pertinente trouvee dans vos documents."
            })
            return
        await nats_client.publish(Subjects.llm_request(sid), {
            "text": query, "documents": docs, "gender": gender, "accent": accent, "mode": mode
        })
    
    await nats_client.subscribe(Subjects.rag_query("*"), handle_rag_query)
    logger.info("RAG Service ready")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())