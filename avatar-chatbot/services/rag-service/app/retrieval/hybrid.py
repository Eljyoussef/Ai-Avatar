import asyncio
from typing import List, Dict
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, SearchRequest
from opensearchpy import OpenSearch
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger(__name__)

class HybridRetriever:
    def __init__(self, config):
        self.config = config
        self.qdrant = QdrantClient(host=config.qdrant_host, port=config.qdrant_port)
        self.opensearch = OpenSearch(
            hosts=[{"host": config.opensearch_host, "port": config.opensearch_port}]
        )
        self.encoder = SentenceTransformer(config.embedding_model)
        
    async def initialize(self):
        """Setup collections and indices if they don't exist."""
        # Setup Qdrant
        collections = self.qdrant.get_collections().collections
        collection_names = [c.name for c in collections]
        
        if self.config.collection_name not in collection_names:
            self.qdrant.create_collection(
                collection_name=self.config.collection_name,
                vectors_config=VectorParams(
                    size=1024,  # multilingual-e5-large dimension
                    distance=Distance.COSINE
                )
            )
            logger.info(f"Created Qdrant collection: {self.config.collection_name}")
        
        # Setup OpenSearch
        if not self.opensearch.indices.exists(index=self.config.index_name):
            self.opensearch.indices.create(
                index=self.config.index_name,
                body={
                    "settings": {
                        "number_of_shards": 1,
                        "number_of_replicas": 0
                    },
                    "mappings": {
                        "properties": {
                            "text": {"type": "text", "analyzer": "french"},
                            "document_id": {"type": "keyword"},
                            "chunk_id": {"type": "keyword"},
                            "metadata": {"type": "object"}
                        }
                    }
                }
            )
            logger.info(f"Created OpenSearch index: {self.config.index_name}")
    
    async def dense_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Search using dense embeddings in Qdrant."""
        query_vector = self.encoder.encode(query).tolist()
        
        results = self.qdrant.query_points(
            collection_name=self.config.collection_name,
            query=query_vector,
            limit=top_k
        )
        
        return [
            {
                "id": hit.id,
                "score": hit.score,
                "text": hit.payload.get("text", ""),
                "metadata": hit.payload.get("metadata", {})
            }
            for hit in results.points
        ]
    
    async def sparse_search(self, query: str, top_k: int = 20) -> List[Dict]:
        """Search using BM25 in OpenSearch."""
        body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["text", "metadata.title"],
                    "type": "best_fields"
                }
            },
            "size": top_k
        }
        
        results = self.opensearch.search(
            index=self.config.index_name,
            body=body
        )
        
        return [
            {
                "id": hit["_id"],
                "score": hit["_score"],
                "text": hit["_source"].get("text", ""),
                "metadata": hit["_source"].get("metadata", {})
            }
            for hit in results["hits"]["hits"]
        ]
    
    def reciprocal_rank_fusion(
        self, 
        dense_results: List[Dict], 
        sparse_results: List[Dict],
        k: int = 60
    ) -> List[Dict]:
        """Fuse results using Reciprocal Rank Fusion."""
        scores = {}
        
        for rank, doc in enumerate(dense_results):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, {"doc": doc, "score": 0})
            scores[doc_id]["score"] += 1 / (k + rank + 1)
        
        for rank, doc in enumerate(sparse_results):
            doc_id = doc["id"]
            scores[doc_id] = scores.get(doc_id, {"doc": doc, "score": 0})
            scores[doc_id]["score"] += 1 / (k + rank + 1)
        
        # Sort by fused score
        sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
        return [item["doc"] for item in sorted_results]