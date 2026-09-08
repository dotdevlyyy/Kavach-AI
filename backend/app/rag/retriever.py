"""
Kavach AI — RAG Retriever
Implements BM25 full-text search via SQLite FTS5 and vector similarity search.
"""

from typing import List, Dict
from loguru import logger
from tortoise import Tortoise
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embedder import deserialize_embedding


async def _hydrate_batch(chunk_ids: list[str]) -> dict[str, dict]:
    """Single roundtrip: fetch all chunks + their documents for an id list."""
    from app.models.document import Document
    chunks = await KnowledgeChunk.filter(id__in=chunk_ids).select_related("document")
    return {
        str(c.id): {
            "chunk_id": str(c.id),
            "document_id": str(c.document_id),
            "document_name": c.document.original_name if c.document else "",
            "metadata": c.metadata or {},
        }
        for c in chunks
    }


async def search_fts(query: str, limit: int = 5) -> List[Dict]:
    """Search knowledge chunks using SQLite FTS5 (BM25 ranking)."""
    conn = Tortoise.get_connection("default")
    rows = await conn.execute_query_dict(
        """
        SELECT chunk_id, content, document_name, rank
        FROM knowledge_fts
        WHERE knowledge_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        [query, limit],
    )
    return [
        {
            "id": row["chunk_id"],
            "content": row["content"],
            "document_name": row.get("document_name", ""),
            "score": abs(row["rank"]),  # FTS5 rank is negative; lower = better
            "source": "fts5",
        }
        for row in rows
    ]


async def search_vector(query_embedding: list[float], limit: int = 5) -> List[Dict]:
    """Search knowledge chunks using cosine similarity on stored embeddings.

    ponytail: brute-force scan over chunks with embeddings. Fine up to a few thousand
    chunks in SQLite. Upgrade to sqlite-vss or a vector store when chunk count grows
    past that ceiling.
    """
    if not query_embedding:
        return []

    # ponytail: hard cap at 200 chunks per scan — see ceiling note above
    chunks = await KnowledgeChunk.filter(embedding__not_isnull=True).limit(200)
    scored = []
    for chunk in chunks:
        if not chunk.embedding:
            continue
        stored = deserialize_embedding(chunk.embedding)
        if len(stored) != len(query_embedding):
            continue
        dot = sum(a * b for a, b in zip(query_embedding, stored))
        norm_a = sum(a * a for a in query_embedding) ** 0.5
        norm_b = sum(b * b for b in stored) ** 0.5
        if norm_a == 0 or norm_b == 0:
            continue
        similarity = dot / (norm_a * norm_b)
        scored.append({
            "id": str(chunk.id),
            "content": chunk.content,
            "score": similarity,
            "source": "vector",
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:limit]


async def hybrid_search(query: str, limit: int = 5) -> List[Dict]:
    """Combine FTS5 and Vector search using Reciprocal Rank Fusion (RRF).

    RRF formula: score = Σ 1 / (k + rank_i)  where k = 60.
    """
    from app.rag.embedder import generate_embedding

    fts_results = await search_fts(query, limit=limit * 2)
    query_emb = await generate_embedding(query)
    vec_results = await search_vector(query_emb, limit=limit * 2) if query_emb else []

    k = 60
    rrf_scores: Dict[str, float] = {}
    content_map: Dict[str, str] = {}

    for rank, result in enumerate(fts_results):
        rid = result["id"]
        rrf_scores[rid] = rrf_scores.get(rid, 0) + 1.0 / (k + rank + 1)
        content_map[rid] = result["content"]

    for rank, result in enumerate(vec_results):
        rid = result["id"]
        rrf_scores[rid] = rrf_scores.get(rid, 0) + 1.0 / (k + rank + 1)
        content_map[rid] = result["content"]

    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    top_ids = sorted_ids[:limit]
    meta_map = await _hydrate_batch(top_ids)
    out = []
    for rid in top_ids:
        meta = meta_map.get(rid, {})
        out.append({
            "chunk_id": meta.get("chunk_id", rid),
            "document_id": meta.get("document_id", ""),
            "document_name": meta.get("document_name", ""),
            "content": content_map[rid],
            "score": rrf_scores[rid],
            "metadata": meta.get("metadata", {}),
        })
    return out
