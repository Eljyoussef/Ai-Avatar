import os
from dataclasses import dataclass, field

@dataclass
class RAGConfig:
    qdrant_host: str = os.getenv("QDRANT_HOST", "localhost")
    qdrant_port: int = int(os.getenv("QDRANT_PORT", "6333"))
    opensearch_host: str = os.getenv("OPENSEARCH_HOST", "localhost")
    opensearch_port: int = int(os.getenv("OPENSEARCH_PORT", "9200"))
    
    embedding_model: str = "intfloat/multilingual-e5-large"
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    
    dense_top_k: int = 20
    sparse_top_k: int = 20
    final_top_k: int = 5
    
    chunk_size: int = 500
    chunk_overlap: int = 50
    
    collection_name: str = "documents_fr"
    index_name: str = "documents_fr_sparse"