"""
Kavach AI — RAG Retriever
Implements BM25 full-text search via SQLite FTS5 and vector similarity search.
"""

from typing import List, Dict
from loguru import logger
from tortoise import Tortoise
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embedder import deserialize_embedding


async def search_fts(query: str, limit: int = 5) -> List[Dict]:
    """Search knowledge chunks using SQLite FTS5 (BM25 ranking).

    Args:
        query: The search query string.
        limit: Maximum number of results to return.

    Returns:
        List of dicts with id, content, document_name, and BM25 score.
    """
    try:
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
    except Exception as e:
        logger.warning(f"FTS5 search failed (table may not exist yet): {e}")
        # Fallback to basic ORM text search
        chunks = await KnowledgeChunk.filter(content__icontains=query).limit(limit)
        return [
            {
                "id": str(c.id),
                "content": c.content,
                "score": 1.0,
                "source": "icontains_fallback",
            }
            for c in chunks
        ]


async def search_vector(query_embedding: list[float], limit: int = 5) -> List[Dict]:
    """Search knowledge chunks using cosine similarity on stored embeddings.

    Note: SQLite does not natively support vector search. This performs a
    brute-force scan over chunks that have embeddings stored. For production
    scale, consider using sqlite-vss or a dedicated vector store.

    Args:
        query_embedding: The query embedding vector.
        limit: Maximum number of results to return.

    Returns:
        List of dicts with id, content, and cosine similarity score.
    """
    if not query_embedding:
        return []

    try:
        chunks = await KnowledgeChunk.filter(embedding__not_isnull=True).limit(200)
        scored = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            stored = deserialize_embedding(chunk.embedding)
            if len(stored) != len(query_embedding):
                continue
            # Cosine similarity
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
    except Exception as e:
        logger.error(f"Vector search error: {e}")
        return []


async def hybrid_search(query: str, limit: int = 5) -> List[Dict]:
    """Combine FTS5 and Vector search using Reciprocal Rank Fusion (RRF).

    RRF formula: score = Σ 1 / (k + rank_i)  where k = 60.

    Args:
        query: The search query.
        limit: Maximum results to return.

    Returns:
        Merged and re-ranked list of search results.
    """
    from app.rag.embedder import generate_embedding

    # Run both searches in parallel
    fts_results = await search_fts(query, limit=limit * 2)
    query_emb = await generate_embedding(query)
    vec_results = await search_vector(query_emb, limit=limit * 2) if query_emb else []

    # RRF merging
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

    # Sort by RRF score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)

    return [
        {"id": rid, "content": content_map[rid], "score": rrf_scores[rid]}
        for rid in sorted_ids[:limit]
    ]
