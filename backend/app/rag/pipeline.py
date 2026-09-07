"""
Kavach AI — RAG Ingestion Pipeline
Ingests parsed document text chunks into the DB with embeddings.
"""

from loguru import logger
from app.rag.embedder import generate_embedding, serialize_embedding
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk


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
    for i, chunk_text in enumerate(text_chunks):
        try:
            embedding = await generate_embedding(chunk_text)
            embedding_bytes = serialize_embedding(embedding) if embedding else None

            await KnowledgeChunk.create(
                document=document,
                content=chunk_text,
                chunk_index=i,
                embedding=embedding_bytes,
            )
            ingested += 1
        except Exception as e:
            logger.error(f"Failed to ingest chunk {i} for document {document_id}: {e}")

    # Mark document as indexed into the knowledge base
    document.is_knowledge_base = True
    await document.save()

    logger.info(f"Ingested {ingested}/{len(text_chunks)} chunks for document {document_id}")
    return ingested
