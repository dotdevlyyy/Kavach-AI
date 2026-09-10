# 08 — RAG Pipeline & Knowledge Base

## Overview

The RAG (Retrieval-Augmented Generation) pipeline allows the AI to ground its responses in the organization's own documents — SOPs, manuals, past correspondence, engineering standards. Everything stays local.

```
┌──────────────────────────────────────────────────────────────┐
│                    RAG PIPELINE                               │
│                                                              │
│  INGESTION (one-time per document):                          │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐  │
│  │ Upload  │──►│  Parse   │──►│  Chunk   │──►│  Embed   │  │
│  │ PDF/DOC │   │ Extract  │   │ Split    │   │ Ollama   │  │
│  │ TXT/IMG │   │ text     │   │ 512 tok  │   │ embed()  │  │
│  └─────────┘   └──────────┘   └──────────┘   └────┬─────┘  │
│                                                     │        │
│                                              ┌──────▼──────┐ │
│                                              │  SQLite     │ │
│                                              │ knowledge_  │ │
│                                              │ chunks +    │ │
│                                              │ FTS5 index  │ │
│                                              └──────┬──────┘ │
│                                                     │        │
│  RETRIEVAL (per query):                             │        │
│  ┌─────────┐   ┌──────────┐   ┌──────────┐        │        │
│  │ User    │──►│ Embed    │──►│ Search   │◄───────┘        │
│  │ Query   │   │ query    │   │ FTS5 +   │                  │
│  └─────────┘   └──────────┘   │ semantic │                  │
│                                └────┬─────┘                  │
│                                     │                        │
│                               ┌─────▼──────┐                │
│                               │  Rank +    │                │
│                               │  Format    │                │
│                               │  context   │                │
│                               └─────┬──────┘                │
│                                     │                        │
│                               ┌─────▼──────┐                │
│                               │  LLM with  │                │
│                               │  context   │                │
│                               └────────────┘                │
└──────────────────────────────────────────────────────────────┘
```

## Ingestion Pipeline

### Document Parser

```python
# app/rag/parser.py
import fitz  # PyMuPDF
from pathlib import Path

def parse_document(file_path: str) -> str:
    """Extract text from various document formats. Raises ValueError on unsupported types."""
    
    path = Path(file_path)
    ext = path.suffix.lower()

    if ext in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    elif ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext == ".docx":
        return _parse_docx(file_path)
    elif ext == ".csv":
        return _parse_csv(file_path)
    else:
        raise ValueError(f"Unsupported file type for parsing: {ext}")

def _parse_pdf(file_path: str) -> str:
    """Extract text from PDF using PyMuPDF."""
    doc = fitz.open(file_path)
    text_parts = []
    
    for page_num, page in enumerate(doc, 1):
        text = page.get_text("text")
        if text.strip():
            text_parts.append(f"[Page {page_num}]\n{text}")
    
    doc.close()
    
    full_text = "\n\n".join(text_parts)
    
    # If very little text extracted, it's likely a scanned PDF
    if len(full_text.strip()) < 100:
        return None  # Needs OCR via vision model
    
    return full_text
```

### Text Chunker

```python
# app/rag/chunker.py

def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 50,
    separator: str = "\n\n",
) -> list[str]:
    """Split text into overlapping chunks for embedding. Returns plain strings."""

    # First split by separator (paragraphs)
    paragraphs = text.split(separator)

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        # If adding this paragraph would exceed chunk_size
        if len(current_chunk) + len(para) > chunk_size and current_chunk:
            chunks.append({
                "index": chunk_index,
                "content": current_chunk.strip(),
                "char_count": len(current_chunk.strip()),
            })
            chunk_index += 1
            
            # Keep overlap
            words = current_chunk.split()
            overlap_words = words[-chunk_overlap:] if len(words) > chunk_overlap else words
            current_chunk = " ".join(overlap_words) + separator + para
        else:
            current_chunk += separator + para if current_chunk else para
    
    # Add remaining text
    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
```

### Embedder

```python
# app/rag/embedder.py
from ollama import AsyncClient
import struct

EMBED_MODEL = "llama3.2:1b"  # Ollama generates embeddings from any model

async def embed_text(client: AsyncClient, text: str) -> bytes:
    """Generate embedding for a text chunk using Ollama."""
    
    response = await client.embed(
        model=EMBED_MODEL,
        input=text,
    )
    
    # response.embeddings is a list of float lists
    embedding = response.embeddings[0]
    
    # Serialize to bytes for SQLite BLOB storage
    return struct.pack(f'{len(embedding)}f', *embedding)

async def embed_batch(client: AsyncClient, texts: list[str]) -> list[bytes]:
    """Batch embed multiple texts."""
    
    response = await client.embed(
        model=EMBED_MODEL,
        input=texts,
    )
    
    results = []
    for emb in response.embeddings:
        results.append(struct.pack(f'{len(emb)}f', *emb))
    
    return results

def deserialize_embedding(blob: bytes, dim: int = 2048) -> list[float]:
    """Deserialize embedding from BLOB."""
    return list(struct.unpack(f'{dim}f', blob))
```

### Ingestion Orchestrator

```python
# app/rag/pipeline.py
from app.rag.parser import parse_document
from app.rag.chunker import chunk_text
from app.rag.embedder import generate_embedding
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk

async def ingest_document(document_id: str, text_chunks: list[str]) -> int:
    """Embed pre-chunked text and store as KnowledgeChunk rows. Caller chunks."""
    document = await Document.get_or_none(id=document_id)
    if not document:
        return 0
    for i, chunk in enumerate(text_chunks):
        embedding = await generate_embedding(chunk)
        await KnowledgeChunk.create(
            document=document, content=chunk, chunk_index=i, embedding=serialize_embedding(embedding) if embedding else None,
        )
        # FTS5 row inserted explicitly here
    document.is_knowledge_base = True
    await document.save()
    return len(text_chunks)
```

The HTTP entry point (`POST /api/knowledge/index`) does parsing + chunking, creates the `Document` row, then calls `ingest_document(document_id, chunks)` for embedding + storage. FTS5 rows are inserted explicitly inside `ingest_document` (no triggers).

## Retrieval Pipeline

### Hybrid Search (FTS5 + Semantic)

```python
# app/rag/retriever.py
import struct
import math
from tortoise.connections import connections

async def hybrid_search(
    query: str,
    query_embedding: bytes,
    top_k: int = 5,
    alpha: float = 0.5,  # Balance between FTS and semantic
) -> list[dict]:
    """Hybrid search combining FTS5 full-text search and cosine similarity."""
    
    conn = connections.get("default")
    
    # 1. FTS5 full-text search
    fts_results = await conn.execute_query(
        """
        SELECT chunk_id, rank
        FROM knowledge_fts
        WHERE knowledge_fts MATCH ?
        ORDER BY rank
        LIMIT ?
        """,
        [query, top_k * 2]
    )
    
    # 2. Semantic search (cosine similarity on embeddings)
    all_chunks = await conn.execute_query(
        """
        SELECT id, content, embedding, document_id
        FROM knowledge_chunks
        WHERE embedding IS NOT NULL
        """
    )
    
    query_emb = deserialize_embedding(query_embedding)
    
    semantic_scores = []
    for chunk in all_chunks[1]:  # [1] is the rows
        chunk_emb = deserialize_embedding(chunk["embedding"])
        similarity = cosine_similarity(query_emb, chunk_emb)
        semantic_scores.append({
            "chunk_id": chunk["id"],
            "content": chunk["content"],
            "document_id": chunk["document_id"],
            "semantic_score": similarity,
        })
    
    semantic_scores.sort(key=lambda x: x["semantic_score"], reverse=True)
    semantic_top = semantic_scores[:top_k * 2]
    
    # 3. Reciprocal Rank Fusion (RRF)
    rrf_scores = {}
    k = 60  # RRF constant
    
    # Add FTS scores
    for rank, result in enumerate(fts_results[1]):
        chunk_id = result["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + (1 - alpha) / (k + rank + 1)
    
    # Add semantic scores
    for rank, result in enumerate(semantic_top):
        chunk_id = result["chunk_id"]
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0) + alpha / (k + rank + 1)
    
    # 4. Sort by RRF score and return top_k
    sorted_results = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
    
    # 5. Fetch full chunk data
    results = []
    for chunk_id, score in sorted_results:
        chunk = await KnowledgeChunk.get(id=chunk_id).select_related("document")
        results.append({
            "chunk_id": str(chunk.id),
            "document_id": str(chunk.document_id),
            "document_name": chunk.document.original_name,
            "content": chunk.content,
            "score": score,
        })

    return results
```

Cosine similarity is computed inline in `search_vector` (`app/rag/retriever.py`), not as a separate helper. The current implementation scans every embedded chunk; move to a vector index when measured dataset size makes that too slow.

### RAG Prompt Construction

KB context is injected into `POST /api/chat` directly when `enable_knowledge_base=true`: `hybrid_search(query, limit=3)` runs, and the top-3 hits are prepended as a `system` message in the format:

```
Knowledge base context:
[<document_name>] <chunk_content[:400]>
...
```

There is no separate `app/rag/prompt.py` module. The agent loop's planner can also call the `search_knowledge_base` tool for ad-hoc RAG.

## Knowledge Base Management

### Upload & Index Flow

```
1. User uploads document via /knowledge page
2. POST /api/knowledge/index with file(s)
3. Backend:
   a. Keep uploaded file in `./data/uploads/`
   b. Parse text (PyMuPDF for PDF, raw for TXT/MD)
   c. If scanned (no text extracted), use Qwen2.5-VL for OCR
   d. Chunk text (512 words, 64-word overlap by default)
   e. Embed each chunk via Ollama
   f. Store chunks + embeddings in SQLite
   g. Ingestion transaction explicitly inserts FTS5 rows (no triggers)
4. Frontend shows indexing progress + chunk count
```

`Document.source_upload_id` identifies the originating upload. A partial unique SQLite index makes
indexing idempotent under concurrent requests; duplicates return HTTP 409. Startup applies this
additive column/index migration to existing databases without rewriting existing document rows.

### Search Flow

```
1. User asks question with KB enabled
2. Backend:
   a. Embed the query via Ollama
   b. Run hybrid search (FTS5 + semantic cosine similarity)
   c. RRF fusion to combine scores
   d. Top-5 chunks become context
   e. Build RAG prompt with context
   f. Send to LLM for generation
3. Response includes citations to source documents
```

## Supported Document Formats

| Format | Parser | Notes |
|---|---|---|
| `.pdf` (text) | PyMuPDF | Direct text extraction |
| `.pdf` (scanned) | Qwen2.5-VL | OCR via vision model |
| `.txt` | Direct read | UTF-8 |
| `.md` | Direct read | Markdown treated as plain text |
| `.docx` | python-docx | Paragraph extraction |
| `.png/.jpg/.jpeg` | Qwen2.5-VL | OCR via vision model |

## Performance Characteristics

| Operation | Expected Latency | Notes |
|---|---|---|
| Document parsing (10-page PDF) | < 1s | PyMuPDF is very fast |
| Chunking (10-page doc) | < 100ms | CPU-bound, trivial |
| Embedding (single chunk) | ~200ms | Ollama embed API |
| Embedding (50 chunks batch) | ~3s | Batched via Ollama |
| FTS5 search | < 10ms | SQLite in-process |
| Semantic search (1000 chunks) | < 100ms | In-memory cosine similarity |
| Hybrid search (full pipeline) | < 500ms | FTS5 + semantic + RRF |
| Full ingestion (10-page PDF) | ~5-10s | Parse + chunk + embed |

> **Vector search scaling:** `search_vector` currently scans every embedded chunk for complete recall. Switch to a vector index when measured KB size makes the scan too slow.
