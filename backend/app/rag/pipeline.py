from app.rag.embedder import generate_embedding
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk

async def ingest_document(document_id: str, text_chunks: list[str]):
    """Ingest a parsed document's text chunks into the DB and generate embeddings."""
    document = await Document.get_or_none(id=document_id)
    if not document:
        return
        
    for i, chunk_text in enumerate(text_chunks):
        embedding = await generate_embedding(chunk_text)
        await KnowledgeChunk.create(
            document=document,
            content=chunk_text,
            chunk_index=i
            # Vector embedding would be saved here if we use pgvector or similar extension.
        )
    
    document.processed = True
    await document.save()
