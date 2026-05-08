from typing import List, Dict
import re
import logging

logger = logging.getLogger(__name__)

class ContextCompressor:
    def __init__(self, max_tokens: int = 2000):
        self.max_tokens = max_tokens
        
    def compress(self, query: str, documents: List[Dict]) -> List[Dict]:
        """Compress documents to fit context window."""
        compressed = []
        total_tokens = 0
        
        for doc in documents:
            text = doc.get("text", "")
            
            # Simple compression: extract most relevant sentences
            sentences = self._split_sentences(text)
            relevant_sentences = self._select_relevant(query, sentences)
            compressed_text = " ".join(relevant_sentences)
            
            # Estimate tokens (rough: 1 token ≈ 4 chars for French)
            estimated_tokens = len(compressed_text) // 4
            
            if total_tokens + estimated_tokens > self.max_tokens:
                remaining = self.max_tokens - total_tokens
                compressed_text = compressed_text[:remaining * 4]
                compressed.append({**doc, "text": compressed_text})
                break
            
            total_tokens += estimated_tokens
            compressed.append({**doc, "text": compressed_text})
        
        return compressed
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        return re.split(r'[.!?;]+\s*', text)
    
    def _select_relevant(self, query: str, sentences: List[str]) -> List[str]:
        """Select sentences most relevant to query."""
        query_terms = set(query.lower().split())
        
        scored_sentences = []
        for sentence in sentences:
            sentence_terms = set(sentence.lower().split())
            overlap = len(query_terms & sentence_terms)
            if overlap > 0:
                scored_sentences.append((sentence, overlap))
        
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Return top 60% most relevant sentences
        cutoff = max(1, int(len(scored_sentences) * 0.6))
        return [s[0] for s in scored_sentences[:cutoff]] if scored_sentences else sentences[:3]