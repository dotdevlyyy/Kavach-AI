"""Knowledge base ingestion, search, listing, and deletion."""

import asyncio
from typing import Literal
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from pydantic import BaseModel, Field, field_validator, model_validator
from tortoise.exceptions import IntegrityError

from app.core.paths import resolve_upload_path
from app.models.document import Document
from app.models.file_upload import FileUpload
from app.models.knowledge_chunk import KnowledgeChunk
from app.rag.chunker import chunk_text
from app.rag.embedder import generate_embedding
from app.rag.parser import parse_document
from app.rag.pipeline import ingest_document
from app.rag.retriever import hybrid_search, search_fts, search_vector
from app.schemas.responses import (
    ActionResponse,
    KnowledgeDocumentsResponse,
    KnowledgeIndexResponse,
    KnowledgeSearchResponse,
)

router = APIRouter(prefix="/api/knowledge", tags=["Knowledge"])


class IndexRequest(BaseModel):
    file_id: UUID
    chunk_size: int = Field(default=512, ge=32, le=2048)
    chunk_overlap: int = Field(default=64, ge=0, le=512)

    @model_validator(mode="after")
    def overlap_must_be_smaller(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        return self


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2_000)
    top_k: int = Field(default=5, ge=1, le=50)
    search_type: Literal["fts", "semantic", "hybrid"] = "hybrid"

    @field_validator("query")
    @classmethod
    def query_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("query required")
        return value


async def _extract_upload_text(upload: FileUpload) -> str:
    if upload.file_type == "image":
        from app.tools.ocr_extract import extract_text_from_image

        return await extract_text_from_image(file_id=str(upload.id))

    path = resolve_upload_path(upload.stored_path)
    if not path.is_file():
        raise FileNotFoundError(path)
    text = await asyncio.wait_for(asyncio.to_thread(parse_document, str(path)), timeout=60)
    if upload.file_type == "pdf" and len(text.strip()) < 10:
        from app.tools.ocr_extract import extract_text_from_image

        return await extract_text_from_image(file_id=str(upload.id))
    return text


@router.post("/index", response_model=KnowledgeIndexResponse)
async def index_document(request: IndexRequest):
    upload = await FileUpload.get_or_none(id=request.file_id)
    if not upload:
        raise HTTPException(status_code=404, detail="File not found")
    if upload.file_type not in {"pdf", "docx", "txt", "md", "csv", "image"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type for indexing: {upload.file_type}",
        )
    try:
        path = resolve_upload_path(upload.stored_path)
    except ValueError:
        raise HTTPException(status_code=404, detail="File content not found")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="File content not found")
    duplicate = await Document.get_or_none(source_upload_id=upload.id)
    if duplicate:
        raise HTTPException(status_code=409, detail="File is already indexed")

    try:
        text = await _extract_upload_text(upload)
    except Exception as exc:
        logger.exception(f"Document parse failed for {upload.id}: {exc}")
        raise HTTPException(status_code=422, detail="Document parsing failed")
    if not text or len(text.strip()) < 10 or text.startswith("Error"):
        raise HTTPException(status_code=422, detail="No extractable text found")

    chunks = chunk_text(
        text,
        chunk_size=request.chunk_size,
        overlap_size=request.chunk_overlap,
    )
    document = Document(
        filename=upload.original_name,
        original_name=upload.original_name,
        file_path=str(path),
        file_type=upload.file_type,
        file_size=upload.file_size,
        mime_type=upload.mime_type,
        source_upload_id=upload.id,
        is_knowledge_base=False,
    )
    try:
        ingested = await ingest_document(document, chunks)
    except IntegrityError:
        raise HTTPException(status_code=409, detail="File is already indexed")
    except Exception as exc:
        logger.exception(f"Document indexing failed for {upload.id}: {exc}")
        raise HTTPException(status_code=500, detail="Document indexing failed")

    return {
        "document_id": str(document.id),
        "filename": upload.original_name,
        "chunks_created": ingested,
        "chunks_requested": len(chunks),
    }


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search(request: SearchRequest):
    if request.search_type == "fts":
        results = await search_fts(request.query, limit=request.top_k)
    elif request.search_type == "semantic":
        query_embedding = await generate_embedding(request.query)
        if not query_embedding:
            raise HTTPException(status_code=503, detail="Embedding model unavailable")
        results = await search_vector(query_embedding, limit=request.top_k)
    else:
        results = await hybrid_search(request.query, limit=request.top_k)

    return {
        "query": request.query,
        "search_type": request.search_type,
        "results": [
            {
                "chunk_id": result.get("chunk_id") or result.get("id"),
                "document_id": result.get("document_id", ""),
                "document_name": result.get("document_name", ""),
                "content": result["content"],
                "score": result.get("score", 0.0),
                "source": result.get("source", request.search_type),
                "metadata": result.get("metadata", {}),
            }
            for result in results
        ],
        "count": len(results),
    }


@router.get("/documents", response_model=KnowledgeDocumentsResponse)
async def list_documents(limit: int = Query(50, ge=1, le=200)):
    documents = await Document.all().order_by("-created_at").limit(limit)
    return {
        "documents": [
            {
                "id": str(document.id),
                "filename": document.filename,
                "original_name": document.original_name,
                "file_type": document.file_type,
                "file_size": document.file_size,
                "is_knowledge_base": document.is_knowledge_base,
                "chunk_count": await document.chunks.all().count(),
                "created_at": str(document.created_at),
            }
            for document in documents
        ],
        "total": await Document.all().count(),
    }


@router.delete("/documents/{document_id}", response_model=ActionResponse)
async def delete_document(document_id: UUID):
    from tortoise.transactions import in_transaction

    document = await Document.get_or_none(id=document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    chunk_ids = [str(chunk.id) for chunk in await KnowledgeChunk.filter(document=document)]

    async with in_transaction() as connection:
        if chunk_ids:
            placeholders = ",".join("?" for _ in chunk_ids)
            await connection.execute_query(
                f"DELETE FROM knowledge_fts WHERE chunk_id IN ({placeholders})",
                chunk_ids,
            )
        await document.delete(using_db=connection)

    return {
        "status": "deleted",
        "document_id": str(document_id),
        "chunks_removed": len(chunk_ids),
    }
