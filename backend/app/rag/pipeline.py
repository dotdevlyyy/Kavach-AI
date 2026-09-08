"""
Kavach AI — RAG Ingestion Pipeline
Ingests parsed document text chunks into the DB with embeddings, plus FTS5 index.
"""

from loguru import logger
from tortoise import Tortoise
from app.rag.embedder import generate_embedding, serialize_embedding
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk


async def _index_chunk_in_fts(chunk_id: str, content: str, document_name: str) -> None:
    """Populate the FTS5 virtual table explicitly (no triggers)."""
    conn = Tortoise.get_connection("default")
    await conn.execute_query(
        "INSERT INTO knowledge_fts(chunk_id, content, document_name) VALUES (?, ?, ?)",
        [chunk_id, content, document_name],
    )


async def ingest_document(document_id: str, text_chunks: list[str]) -> int:
    """Ingest a parsed document's text chunks into the DB and generate embeddings.

    Args:
        document_id: UUID of the Document record.
        text_chunks: List of text chunks from the parser/chunker.

    Returns:
        Number of chunks successfully ingested.
    """
    document = await Document.get_or_none(id=document_id)
    if not document:
        logger.warning(f"Document {document_id} not found for ingestion")
        return 0

    ingested = 0
    for i, chunk in enumerate(text_chunks):
        try:
            embedding = await generate_embedding(chunk)
            embedding_bytes = serialize_embedding(embedding) if embedding else None

            new_chunk = await KnowledgeChunk.create(
                document=document,
                content=chunk,
                chunk_index=i,
                embedding=embedding_bytes,
            )
            await _index_chunk_in_fts(
                str(new_chunk.id), chunk, document.original_name
            )
            ingested += 1
        except Exception as e:
            logger.error(f"Failed to ingest chunk {i} for document {document_id}: {e}")

    # Mark document as indexed into the knowledge base
    document.is_knowledge_base = True
    await document.save()

    logger.info(f"Ingested {ingested}/{len(text_chunks)} chunks for document {document_id}")
    return ingested

