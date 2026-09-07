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

async def parse_document(file_path: str) -> str:
    """Extract text from various document formats."""
    
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext == ".pdf":
        return _parse_pdf(file_path)
    elif ext == ".txt":
        return path.read_text(encoding="utf-8")
    elif ext == ".md":
        return path.read_text(encoding="utf-8")
    elif ext == ".docx":
        return _parse_docx(file_path)
    elif ext in {".png", ".jpg", ".jpeg", ".webp", ".tiff"}:
        # For images, use Qwen2.5-VL for OCR
        return None  # Handled separately by OCR tool
    else:
        return f"Unsupported format: {ext}"

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
) -> list[dict]:
    """Split text into overlapping chunks for embedding."""
    
    # First split by separator (paragraphs)
    paragraphs = text.split(separator)
    
    chunks = []
    current_chunk = ""
    chunk_index = 0
    
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
        chunks.append({
            "index": chunk_index,
            "content": current_chunk.strip(),
            "char_count": len(current_chunk.strip()),
        })
    
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
from app.rag.embedder import embed_text
from app.models.document import Document
from app.models.knowledge_chunk import KnowledgeChunk

async def ingest_document(file_path: str, original_name: str, ollama_client) -> str:
    """Full ingestion pipeline: parse → chunk → embed → store."""
    
    # 1. Parse
    text = await parse_document(file_path)
    if text is None:
        return "Document requires OCR (scanned). Use vision model for extraction."
    
    # 2. Create document record
    doc = await Document.create(
        filename=Path(file_path).name,
        original_name=original_name,
        file_path=file_path,
        file_type=Path(file_path).suffix[1:],
        file_size=Path(file_path).stat().st_size,
        mime_type="application/pdf",
        is_knowledge_base=True,
    )
    
    # 3. Chunk
    chunks = chunk_text(text, chunk_size=512, chunk_overlap=50)
    
    # 4. Embed and store
    for chunk_data in chunks:
        embedding_blob = await embed_text(ollama_client, chunk_data["content"])
        
        await KnowledgeChunk.create(
            document=doc,
            chunk_index=chunk_data["index"],
            content=chunk_data["content"],
            embedding=embedding_blob,
            metadata={"char_count": chunk_data["char_count"]},
        )
    
    # 5. Update FTS5 index (happens automatically via trigger)
    
    return f"Indexed {len(chunks)} chunks from '{original_name}'"
```

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
            "metadata": chunk.metadata,
        })
    
    return results

def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

### RAG Prompt Construction

```python
# app/rag/prompt.py

RAG_SYSTEM_PROMPT = """You are Kavach AI, a sovereign on-premise AI assistant for industrial organizations.

You have access to the organization's knowledge base. Use the following context from internal documents to answer the user's question. Always cite the source document when using information from the context.

If the context doesn't contain relevant information, say so honestly. Do not make up information.

--- CONTEXT FROM KNOWLEDGE BASE ---
{context}
--- END CONTEXT ---

Answer the user's question based on the above context and your general knowledge."""

def build_rag_prompt(query: str, search_results: list[dict]) -> str:
    """Build the RAG prompt with retrieved context."""
    
    context_parts = []
    for i, result in enumerate(search_results, 1):
        context_parts.append(
            f"[Source {i}: {result['document_name']}]\n{result['content']}"
        )
    
    context = "\n\n".join(context_parts)
    return RAG_SYSTEM_PROMPT.format(context=context)
```

## Knowledge Base Management

### Upload & Index Flow

```
1. User uploads document via /knowledge page
2. POST /api/knowledge/index with file(s)
3. Backend:
   a. Save file to ./data/knowledge/
   b. Parse text (PyMuPDF for PDF, raw for TXT/MD)
   c. If scanned (no text extracted), use Qwen2.5-VL for OCR
   d. Chunk text (512 tokens, 50 token overlap)
   e. Embed each chunk via Ollama
   f. Store chunks + embeddings in SQLite
   g. FTS5 trigger auto-indexes for full-text search
4. Frontend shows indexing progress + chunk count
```

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
