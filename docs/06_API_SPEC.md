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
    message: str                           # User's message text
    conversation_id: str | None = None     # Existing conversation UUID, or None for new
    files: list[str] = []                  # List of uploaded file UUIDs to attach (alias: file_ids)
    model_override: str | None = None      # Force specific model (bypass router)
    system_prompt: str | None = None       # Custom system prompt (only for new conversations)
    enable_knowledge_base: bool = True     # When true, hybrid-search KB and inject top-3 hits into the prompt
```

**Response (SSE stream):**
```
event: metadata
data: {"conversation_id": "uuid", "model": "llama3.2:1b", "task_type": "general_chat"}

event: token
data: {"content": "The"}

event: token
data: {"content": " inspection"}

...

event: done
data: {"conversation_id": "uuid", "message_id": "uuid", "assistant_message_id": "uuid", "model": "llama3.2:1b", "status": "completed", "words_in": 342, "words_out": 187}
```

Note: `words_in` / `words_out` are whitespace-split word counts (not tokens — Ollama SDK does not expose tokenizer counts).

**Error:**
```python
# Returned inline in SSE stream as event: error
{"error": "human-readable message"}
```

---

### POST `/api/agent/execute`

Start an agentic multi-step task.

**Request:**
```python
class AgentExecuteRequest(pydantic.BaseModel):
    task_description: str                  # What the agent should do
    conversation_id: str | None = None     # Attach to existing conversation
    files: list[str] = []                  # File UUIDs to make available (alias: file_ids)
    model_override: str | None = None      # Force specific model (bypass router)
    system_prompt: str | None = None       # Custom system prompt (only for new conversations)
    max_steps: int = 10                    # Maximum agent loop iterations
    # KB access: agent uses `search_knowledge_base` tool in its plan when needed;
    # no top-level flag required.
```

**Response (SSE stream):** emits `metadata`, `step` (with `type` ∈ {plan, act, observe, reflect}), `tool_result`, `token`, and `done` events. See `app/agent/loop.py` for canonical shape.

---

### POST `/api/files/upload`

Upload one or more files.

**Request:** `multipart/form-data`
- `files`: One or more files
- `conversation_id` (optional): Associate with conversation

**Response:**
```python
# Plain dict (no msgspec)
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
        }
    ]
}
```

---

### GET `/api/models/ps`

Check which models are currently loaded in memory.

**Response:** plain dict with `running[]`. Each entry has `name`, `size_vram`, `expires_at`, `processor`.

---

### GET `/api/network` (alias: `/api/network/connections`)

Live network connections for sovereignty proof.

**Response:** plain dict with `connections[]` (each: `local_address`, `remote_address`, `protocol`, `status`, `process`, `is_local`), plus `local_count`, `external_count`, `is_air_gapped`, `timestamp`.

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
    "models": {"llama3.2:1b": true, ...},
}
```

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

## Error Handling

Errors return as:
- HTTP `4xx` / `5xx` JSON body `{"detail": "..."}` for sync endpoints
- SSE `event: error\ndata: {"error": "..."}` inside streams

| Status Code | Meaning |
|---|---|
| 400 | Invalid request (missing fields, invalid file type) |
| 404 | Conversation / task / file not found |
| 422 | Validation error |
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
