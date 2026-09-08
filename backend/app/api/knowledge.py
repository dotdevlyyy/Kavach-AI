"""
Kavach AI — Knowledge Base API
Endpoints for indexing uploaded files into the RAG pipeline and searching the KB.
"""

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.models.file_upload import FileUpload
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.parser import parse_document
from app.rag.chunker import chunk_text
from app.rag.pipeline import ingest_document
from app.rag.retriever import hybrid_search, search_fts, search_vector
from app.rag.embedder import generate_embedding

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


class IndexRequest(BaseModel):
    file_id: str
    chunk_size: int = 512
    chunk_overlap: int = 64


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    search_type: str = "hybrid"  # "fts" | "semantic" | "hybrid"


@router.post("/index")
async def index_document(req: IndexRequest):
    """
    POST /api/knowledge/index
    Parse an uploaded FileUpload into chunks, embed, and store as Document + KnowledgeChunk rows.
    """
    upload = await FileUpload.get_or_none(id=req.file_id)
    if not upload:
        raise HTTPException(status_code=404, detail="File not found")

    if upload.file_type not in ("pdf", "docx", "txt", "csv"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type for indexing: {upload.file_type}",
        )

    try:
        text = parse_document(upload.stored_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Parse failed: {e}")

    if not text or len(text.strip()) < 10:
        raise HTTPException(
            status_code=422,
            detail="No extractable text (likely scanned — use OCR tool first)",
        )

    chunks = chunk_text(text, chunk_size=req.chunk_size, overlap_size=req.chunk_overlap)

    doc = await Document.create(
        filename=upload.original_name,
        original_name=upload.original_name,
        file_path=upload.stored_path,
        file_type=upload.file_type,
        file_size=upload.file_size,
        mime_type=upload.mime_type,
        is_knowledge_base=False,
    )

    ingested = await ingest_document(str(doc.id), chunks)

    return {
        "document_id": str(doc.id),
        "filename": upload.original_name,
        "chunks_created": ingested,
        "chunks_requested": len(chunks),
    }


@router.post("/search")
async def search(req: SearchRequest):
    """
    POST /api/knowledge/search
    Hybrid FTS5 + vector similarity search via RRF.
    """
    if not req.query.strip():
        raise HTTPException(status_code=400, detail="query required")

    if req.search_type == "fts":
        results = await search_fts(req.query, limit=req.top_k)
    elif req.search_type == "semantic":
        query_embedding = await generate_embedding(req.query)
        if not query_embedding:
            raise HTTPException(status_code=503, detail="Embedding model unavailable")
        results = await search_vector(query_embedding, limit=req.top_k)
    elif req.search_type == "hybrid":
        results = await hybrid_search(req.query, limit=req.top_k)
    else:
        raise HTTPException(status_code=400, detail=f"Unknown search_type: {req.search_type}")

    return {
        "query": req.query,
        "search_type": req.search_type,
        "results": [
            {
                "chunk_id": r.get("chunk_id", r["id"]),
                "document_id": r.get("document_id", ""),
                "document_name": r.get("document_name", ""),
                "content": r["content"],
                "score": r.get("score", 0.0),
                "source": r.get("source", "unknown"),
                "metadata": r.get("metadata", {}),
            }
            for r in results
        ],
        "count": len(results),
    }


@router.get("/documents")
async def list_documents(limit: int = Query(50, ge=1, le=200)):
    """GET /api/knowledge/documents — List all documents in the knowledge base."""
    docs = await Document.all().order_by("-created_at").limit(limit)
    return {
        "documents": [
            {
                "id": str(d.id),
                "filename": d.filename,
                "original_name": d.original_name,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "is_knowledge_base": d.is_knowledge_base,
                "chunk_count": await d.chunks.all().count(),
                "created_at": str(d.created_at),
            }
            for d in docs
        ],
        "total": await Document.all().count(),
    }


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """DELETE /api/knowledge/documents/{id} — Drop document, its chunks, and FTS5 rows."""
    from tortoise import Tortoise
    doc = await Document.get_or_none(id=document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    chunk_ids = [str(c.id) for c in await KnowledgeChunk.filter(document=doc)]
    if chunk_ids:
        conn = Tortoise.get_connection("default")
        await conn.execute_query(
            f"DELETE FROM knowledge_fts WHERE chunk_id IN ({','.join('?' * len(chunk_ids))})",
            chunk_ids,
        )

    chunks_deleted = len(chunk_ids)
    await doc.delete()
    return {
        "status": "deleted",
        "document_id": document_id,
        "chunks_removed": chunks_deleted,
    }
