from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)

class SemanticMemory:
    """Qdrant-based semantic memory for long-term facts."""
    
    def __init__(self, host: str = "localhost", port: int = 6333):
        self.client = QdrantClient(host=host, port=port)
        self.collection = "user_facts"
        self.encoder = SentenceTransformer("intfloat/multilingual-e5-large")
        
    async def initialize(self):
        """Create collection if not exists."""
        collections = self.client.get_collections().collections
        names = [c.name for c in collections]
        
        if self.collection not in names:
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created semantic memory collection: {self.collection}")
    
    async def store_fact(self, user_id: str, fact: str, metadata: Dict = None):
        """Store a fact about the user."""
        vector = self.encoder.encode(fact).tolist()
        
        point = PointStruct(
            id=np.random.randint(0, 2**63),
            vector=vector,
            payload={
                "user_id": user_id,
                "fact": fact,
                "metadata": metadata or {},
                "timestamp": str(datetime.now())
            }
        )
        
        self.client.upsert(
            collection_name=self.collection,
            points=[point]
        )
    
    async def search_facts(self, user_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Search relevant facts for a user."""
        query_vector = self.encoder.encode(query).tolist()
        
        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            query_filter={
                "must": [{"key": "user_id", "match": {"value": user_id}}]
            },
            limit=limit
        )
        
        return [
            {
                "fact": hit.payload["fact"],
                "score": hit.score,
                "metadata": hit.payload.get("metadata", {})
            }
            for hit in results
        ]