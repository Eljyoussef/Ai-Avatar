import re
from typing import List, Dict

class SemanticChunker:
    """Intelligent document chunking with overlap."""
    
    def __init__(self, chunk_size: int = 500, overlap: int = 50):
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk(self, text: str, metadata: Dict = None) -> List[Dict]:
        """Chunk text into semantic segments."""
        
        # Level 1: Split by headings/sections
        sections = self._split_by_headings(text)
        
        chunks = []
        chunk_id = 0
        
        for section in sections:
            section_chunks = self._create_chunks(section)
            
            for chunk_text in section_chunks:
                chunks.append({
                    "text": chunk_text,
                    "chunk_id": f"{metadata.get('document_id', 'doc')}_chunk_{chunk_id}",
                    "metadata": {
                        **(metadata or {}),
                        "chunk_index": chunk_id,
                        "char_count": len(chunk_text)
                    }
                })
                chunk_id += 1
        
        return chunks
    
    def _split_by_headings(self, text: str) -> List[str]:
        """Split by markdown-style headings."""
        # Split on headings (##, ###, etc.)
        parts = re.split(r'\n(?:#{1,6}\s+.+)\n', text)
        return [p.strip() for p in parts if p.strip()]
    
    def _create_chunks(self, text: str) -> List[str]:
        """Create overlapping chunks from text."""
        words = text.split()
        chunks = []
        
        if len(words) <= self.chunk_size:
            return [text]
        
        start = 0
        while start < len(words):
            end = start + self.chunk_size
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            start += (self.chunk_size - self.overlap)
        
        return chunks