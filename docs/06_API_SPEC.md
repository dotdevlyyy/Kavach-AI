# 06 — API Specification

> **Framework:** FastAPI
> **Serialization:** Pydantic `BaseModel` (request bodies), plain dicts (responses + SSE payloads)
> **Streaming:** Server-Sent Events (SSE)
> **Base URL:** `http://localhost:8000/api`

## API Overview

| Method | Endpoint | Purpose | Streaming |
|---|---|---|---|
| POST | `/api/chat` | Send message, get AI response | ✓ SSE |
| POST | `/api/chat/stop` | Stop an in-progress generation | ✗ |
| GET | `/api/chat/conversations` | List all conversations | ✗ |
| GET | `/api/chat/conversations/{id}` | Get conversation with messages | ✗ |
| DELETE | `/api/chat/conversations/{id}` | Delete conversation | ✗ |
| POST | `/api/agent/execute` | Start agentic task | ✓ SSE |
| GET | `/api/agent/tasks` | List recent agent tasks | ✗ |
| GET | `/api/agent/tasks/{id}` | Get task status + steps | ✗ |
| POST | `/api/agent/tasks/{id}/cancel` | Cancel running task | ✗ |
| POST | `/api/files/upload` | Upload file(s) | ✗ |
| GET | `/api/files/{id}` | Get file metadata | ✗ |
| GET | `/api/files/download/{id}` | Download file (also serves agent-generated docs) | ✗ |
| GET | `/api/files/{id}/preview` | Get file preview (text/image/unsupported) | ✗ |
| POST | `/api/knowledge/index` | Index document(s) into KB | ✗ |
| POST | `/api/knowledge/search` | Search knowledge base | ✗ |
| GET | `/api/knowledge/documents` | List KB documents | ✗ |
| DELETE | `/api/knowledge/documents/{id}` | Remove document from KB | ✗ |
| GET | `/api/models` | List available models + status | ✗ |
| GET | `/api/models/ps` | Currently loaded models (VRAM) | ✗ |
| GET | `/api/network` | Live network connections (alias `/api/network/connections`) | ✗ |
| GET | `/api/network/logs` | Historical network logs | ✗ |
| GET | `/api/health` | System health check | ✗ |

---

## Detailed Endpoints

### POST `/api/chat`

Send a message and receive a streaming AI response.

**Request:**
```python
class ChatRequest(pydantic.BaseModel):
    message: str                           # 1-20,000 chars; blank is HTTP 422
    conversation_id: str | None = None     # Existing conversation UUID, or None for new
    files: list[str] = []                  # Uploaded UUIDs; files + file_ids combined max: 10
    model_override: str | None = None      # Force specific model (bypass router)
    system_prompt: str | None = None       # Custom system prompt (only for new conversations)
    enable_knowledge_base: bool = True     # When true, hybrid-search KB and inject top-3 hits into the prompt
```

**Response (SSE stream):**
```
event: metadata
data: {"conversation_id": "uuid", "message_id": "uuid", "model": "llama3.2:1b", "task_type": "general_chat", "confidence": 0.95, "reasoning": "...", "accepted_file_ids": ["uuid"]}

event: token
data: {"content": "The"}

event: token
data: {"content": " inspection"}

...

event: done
data: {"conversation_id": "uuid", "message_id": "uuid", "assistant_message_id": "uuid", "model": "llama3.2:1b", "status": "completed", "words_in": 342, "words_out": 187, "truncated": false, "error": null}
```

Note: `words_in` / `words_out` are whitespace-split word counts (not tokens — Ollama SDK does not expose tokenizer counts).

Attachment IDs are resolved before streaming. Chat accepts TXT, Markdown, CSV, JSON, source code,
PDF, DOCX, and images. Other uploaded formats return HTTP 422. Missing, unreadable, or out-of-root
files also return HTTP 422. Combined attachment bytes are capped at 40 MB, images at 4, extracted
text at 100,000 characters, PDF OCR at 20 pages, and the full chat pipeline at 120 seconds;
pre-stream attachment timeout returns HTTP 504. `accepted_file_ids` confirms which IDs reached
prompt construction. Existing conversations keep their original
`model_override` and `system_prompt`; request values apply only when creating a conversation.

**Error:**
```python
# Returned inline in SSE stream as event: error
{"error": "human-readable message"}
```

---

`POST /api/chat/stop` returns `cancellation_requested`, HTTP 404 when no generation is running,
and HTTP 400 for a missing or malformed `conversation_id`.

### POST `/api/agent/execute`

Start an agentic multi-step task.

**Request:**
```python
class AgentExecuteRequest(pydantic.BaseModel):
    task_description: str                  # 1-20,000 chars; blank is HTTP 422
    conversation_id: str | None = None     # Attach to existing conversation
    files: list[str] = []                  # File UUIDs; files + file_ids combined max: 10
    model_override: str | None = None      # Force specific model (bypass router)
    system_prompt: str | None = None       # Custom system prompt (only for new conversations)
    max_steps: int = 10                    # Maximum agent loop iterations
    # KB access: agent uses `search_knowledge_base` tool in its plan when needed;
    # no top-level flag required.
```

**Response (SSE stream):** emits `metadata`, `step` (with `type` ∈ {plan, act, observe, reflect}), `tool_result`, `token`, and `done` events. See `app/agent/loop.py` for canonical shape.

---

Agent attachments are limited to PDF and images and validated before streaming. Successful step output flows into later steps
through a bounded 16,000-character evidence context; each step contributes at most 4,000
characters. `done.status` is `completed`, `failed`, or `cancelled`. `done.output_files` lists
generated-file UUIDs. Every agent `done` event also contains `task_id`, `total_steps`, `truncated`,
and nullable `error`. Cancel returns `cancellation_signaled`, `not_running` for an existing idle
task, or HTTP 404 for an unknown task.

### POST `/api/files/upload`

Upload one or more files.

**Request:** `multipart/form-data`
- `files`: One or more files
- `conversation_id` (optional): Associate with conversation

Limits: 10 files per request and 20 MB compressed bytes per file. Upload accepts PDF, DOCX, XLSX,
CSV, TXT, Markdown, JSON, common images, and common source-code extensions. Chat attachment and KB
indexing are narrower contracts: chat accepts TXT, Markdown, CSV, JSON, source code, PDF, DOCX, and
images; agent accepts PDF and images; KB indexing accepts PDF, DOCX, CSV, TXT, Markdown, and images.
Browser MIME variants include `application/vnd.ms-excel` for CSV and
`application/javascript` for JavaScript. WebP requires both RIFF and WEBP markers. DOCX/XLSX
archives require their standard internal member, at most 10,000 members, and at most 100 MB total
expanded size. Size overflow returns HTTP 413; type/content mismatch returns HTTP 400.

**Response:**
```python
# JSON response encoded with msgspec
{
    "files": [
        {
            "id": "uuid",
            "original_name": "report.pdf",
            "file_type": "pdf",
            "file_size": 12345,
            "mime_type": "application/pdf",
        }
    ]
}
```

Generated downloads use standard media types for PDF, DOCX, XLSX, and PPTX rather than
`application/octet-stream`. Generated output metadata is derived from its UUID-prefixed filename;
generated outputs are not persisted as `FileUpload` rows.

---

### POST `/api/knowledge/search`

Search the local knowledge base.

**Request:**
```python
class SearchRequest(pydantic.BaseModel):
    query: str
    top_k: int = 5
    search_type: str = "hybrid"  # "fts" (full-text), "semantic" (vector cosine), "hybrid" (RRF fusion)
```

**Response:** plain dict with `query`, `search_type`, `results[]`, `count`. Each result has `chunk_id`, `document_id`, `document_name`, `content`, `score`, `source` (`fts5` | `vector`), `metadata`.

All three search modes hydrate the same citation metadata. Semantic search returns HTTP 503 when
the embedding model is unavailable.

### POST `/api/knowledge/index`

Index one or more documents into the knowledge base (chunk → embed → store).

**Request:** `application/json`
```python
class IndexRequest(pydantic.BaseModel):
    file_id: str                           # FileUpload UUID to ingest
    chunk_size: int = 512                  # Target words per chunk
    chunk_overlap: int = 64                # Overlap words between consecutive chunks
```

**Response:** plain dict with `document_id`, `filename`, `chunks_created`, `chunks_requested`.

Indexing is idempotent per source upload. Duplicate or concurrent duplicate requests return HTTP
409. Stored paths must remain under `data/uploads`; missing or invalid content is rejected.

---

### GET `/api/models`

List available models and their status.

**Response:**
```python
# Plain dict
{
    "models": [
        {
            "name": "llama3.2:1b",
            "purpose": "general_chat",
            "size_gb": 0.8,
            "is_loaded": True,
            "installed": True,
            "loaded": True,
            "ready": True,
        }
    ]
}
```

---

The model list includes all three chat models and `nomic-embed-text`.

### GET `/api/models/ps`

Check which models are currently loaded in memory.

**Response:** plain dict with `running[]`. Each entry has `name`, `size_vram`, `expires_at`, `processor`.

---

### GET `/api/network` (alias: `/api/network/connections`)

Live network connections for sovereignty proof.

**Response:** plain dict with `connections[]` (each: `local_address`, `remote_address`, `protocol`, `status`, `process`, `is_local`), plus `local_count`, `external_count`, `is_air_gapped`, `air_gap_status`, `monitor_error`, and `timestamp`. Before a trustworthy snapshot or after collection failure, `is_air_gapped` and `timestamp` may be null and `air_gap_status` is `unknown`.

---

### GET `/api/network/logs`

Historical `NetworkLog` rows. Populated by a background `asyncio.create_task` snapshotter
started in `app/main.py` lifespan (ticks every 30s, also fires on each `GET /api/network`
when `?persist=true`). Returns the 50 most recent rows.

**Response:** plain dict with `logs[]` (each: `timestamp`, `local_addr`, `remote_addr`,
`protocol`, `status`, `process_name`, `is_local`) and `total`.

---

### GET `/api/health`

System health check.

**Response:**
```python
# Plain dict
{
    "status": "healthy",          # "healthy" | "degraded" | "unhealthy"
    "app": "Kavach AI",
    "version": "1.0.0",
    "air_gapped": true,
    "uptime_seconds": 1234,
    "disk_usage_gb": 12.3,
    "ollama": {"status": "connected", "host": "http://localhost:11434", "latency_ms": 42},
    "database": {"status": "connected", "path": "./data/kavach.db"},
    "models": {
        "llama3.2:1b": {"name": "llama3.2:1b", "kind": "chat", "installed": true, "loaded": true, "ready": true},
        "nomic-embed-text": {"name": "nomic-embed-text", "kind": "embedding", "installed": true, "loaded": true, "ready": true}
    },
}
```

`healthy` requires DB connectivity, Ollama connectivity, and all three chat models plus the
embedding model installed and loaded. Installed but unloaded models produce `degraded`; missing
models, unavailable Ollama, or unavailable DB produce `unhealthy`. When Ollama is unreachable,
`installed` and `loaded` are `null` because inventory state is unknown; `ready` remains `false`.

---

## SSE Streaming Format

All streaming endpoints use standard Server-Sent Events:

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive

event: <event_type>
data: <json_payload>

```

The frontend consumes these via the `EventSource` API or `fetch` with `ReadableStream`.

`POST` streams normally require `fetch` because browser `EventSource` only performs GET. OpenAPI
advertises both streaming endpoints as `text/event-stream`.

## Error Handling

Errors return as:
- HTTP `4xx` / `5xx` JSON body `{"detail": "..."}` for sync endpoints
- SSE `event: error\ndata: {"error": "..."}` inside streams

| Status Code | Meaning |
|---|---|
| 400 | Invalid file type/content or malformed imperative action payload |
| 404 | Conversation / task / file not found |
| 409 | Source upload is already indexed |
| 413 | Upload, archive expansion, or aggregate attachment limit exceeded |
| 422 | Pydantic validation, missing/unreadable attachment, or unparseable document |
| 500 | Internal server error (Ollama down, tool crash) |
| 503 | Model not loaded / Ollama unreachable / embedding model unavailable |

## CORS Configuration

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend only
    allow_methods=["*"],
    allow_headers=["*"],
)
```
