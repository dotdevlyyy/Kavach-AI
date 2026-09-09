"""Atomic knowledge chunk and FTS ingestion."""

from loguru import logger
from tortoise.transactions import in_transaction

from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.embedder import generate_embeddings, serialize_embedding


async def ingest_document(document: Document, text_chunks: list[str]) -> int:
    """Embed and atomically store a new document, its chunks, and FTS rows."""
    if not text_chunks:
        raise ValueError("Document produced no chunks")

    embeddings = await generate_embeddings(text_chunks)
    async with in_transaction() as connection:
        await document.save(using_db=connection, force_create=True)
        for index, (content, embedding) in enumerate(zip(text_chunks, embeddings, strict=True)):
            chunk = await KnowledgeChunk.create(
                using_db=connection,
                document=document,
                content=content,
                chunk_index=index,
                embedding=serialize_embedding(embedding) if embedding else None,
            )
            await connection.execute_query(
                "INSERT INTO knowledge_fts(chunk_id, content, document_name) VALUES (?, ?, ?)",
                [str(chunk.id), content, document.original_name],
            )

        document.is_knowledge_base = True
        await document.save(using_db=connection, update_fields=["is_knowledge_base"])

    logger.info(f"Ingested {len(text_chunks)} chunks for document {document.id}")
    return len(text_chunks)
