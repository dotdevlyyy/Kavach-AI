from typing import List, Dict
from app.models.knowledge_chunk import KnowledgeChunk

async def search_fts(query: str, limit: int = 5) -> List[Dict]:
    """Search knowledge chunks using SQLite FTS5 (BM25)."""
    # A basic ORM filter for now as a placeholder for FTS.
    chunks = await KnowledgeChunk.filter(content__icontains=query).limit(limit)
    return [{"id": str(c.id), "content": c.content, "score": 1.0} for c in chunks]

async def search_vector(query_embedding: list[float], limit: int = 5) -> List[Dict]:
    """Search knowledge chunks using Cosine Similarity on vectors."""
    # Placeholder for vector search
    return []

async def hybrid_search(query: str, limit: int = 5) -> List[Dict]:
    """Combine FTS5 and Vector search using Reciprocal Rank Fusion (RRF)."""
    # Simply returning FTS search for now.
    return await search_fts(query, limit)
