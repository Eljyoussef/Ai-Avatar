from typing import List, Dict
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    def __init__(self, config):
        self.model = CrossEncoder(config.reranker_model)
        
    async def rerank(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Rerank documents using cross-encoder."""
        if not documents:
            return []
        
        # Create query-document pairs
        pairs = [[query, doc["text"]] for doc in documents]
        
        # Score all pairs
        scores = self.model.predict(pairs)
        
        # Combine with documents and sort
        scored_docs = list(zip(documents, scores))
        scored_docs.sort(key=lambda x: x[1], reverse=True)
        
        # Return reranked documents
        return [
            {**doc, "rerank_score": float(score)}
            for doc, score in scored_docs
        ]