import asyncio
from typing import List, Dict
from sentence_transformers import CrossEncoder
import logging

logger = logging.getLogger(__name__)

class CrossEncoderReranker:
    def __init__(self, config):
        self.model = CrossEncoder(config.reranker_model)
        
    async def rerank(self, query: str, documents: List[Dict]) -> List[Dict]:
        if not documents:
            return []
        
        pairs = [[query, doc["text"]] for doc in documents]
        
        # Non-blocking inference
        scores = await asyncio.to_thread(self.model.predict, pairs)
        
        # Build properly structured results
        scored = []
        for doc, score in zip(documents, scores):
            doc_copy = dict(doc)
            doc_copy["rerank_score"] = float(score)
            scored.append((float(score), doc_copy))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored]