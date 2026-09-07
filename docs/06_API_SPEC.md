# 06 — API Specification

> **Framework:** FastAPI
> **Serialization:** msgspec Structs
> **Streaming:** Server-Sent Events (SSE)
> **Base URL:** `http://localhost:8000/api`

## API Overview

| Method | Endpoint | Purpose | Streaming |
|---|---|---|---|
| POST | `/api/chat` | Send message, get AI response | ✓ SSE |
| POST | `/api/chat/stop` | Stop an in-progress generation | ✗ |
| GET | `/api/conversations` | List all conversations | ✗ |
| GET | `/api/conversations/{id}` | Get conversation with messages | ✗ |
| DELETE | `/api/conversations/{id}` | Delete conversation | ✗ |
| POST | `/api/agent/execute` | Start agentic task | ✓ SSE |
| GET | `/api/agent/tasks/{id}` | Get task status + steps | ✗ |
| POST | `/api/agent/tasks/{id}/cancel` | Cancel running task | ✗ |
| POST | `/api/files/upload` | Upload file(s) | ✗ |
| GET | `/api/files/{id}` | Download file | ✗ |
| GET | `/api/files/{id}/preview` | Get file preview (text/image) | ✗ |
| POST | `/api/knowledge/index` | Index document(s) into KB | ✗ |
| POST | `/api/knowledge/search` | Search knowledge base | ✗ |
| GET | `/api/knowledge/documents` | List KB documents | ✗ |
| DELETE | `/api/knowledge/documents/{id}` | Remove document from KB | ✗ |
| GET | `/api/models` | List available models + status | ✗ |
| GET | `/api/models/ps` | Currently loaded models (VRAM) | ✗ |
| GET | `/api/network/connections` | Live network connections | ✗ |
| GET | `/api/network/logs` | Historical network logs | ✗ |
| GET | `/api/health` | System health check | ✗ |

---

## Detailed Endpoints

### POST `/api/chat`

Send a message and receive a streaming AI response.

**Request:**
```python
class ChatRequest(msgspec.Struct):
    message: str                           # User's message text
    conversation_id: str | None = None     # Existing conversation UUID, or None for new
    files: list[str] = []                  # List of uploaded file UUIDs to attach
    model_override: str | None = None      # Force specific model (bypass router)
    system_prompt: str | None = None       # Custom system prompt (only for new conversations)
    enable_knowledge_base: bool = True     # Include KB context in prompt
```

**Response (SSE stream):**
```
event: metadata
data: {"conversation_id": "uuid", "model": "llama3.2:1b", "task_type": "general_chat"}

event: token
data: {"content": "The"}

event: token
data: {"content": " inspection"}

event: token
data: {"content": " report"}

...

event: done
data: {"message_id": "uuid", "tokens_in": 342, "tokens_out": 187, "latency_ms": 2340}
```

**Error:**
```python
class ErrorResponse(msgspec.Struct):
    error: str
    detail: str | None = None
    status_code: int = 500
```

---

### POST `/api/agent/execute`

Start an agentic multi-step task.

**Request:**
```python
class AgentExecuteRequest(msgspec.Struct):
    task_description: str                  # What the agent should do
    conversation_id: str | None = None     # Attach to existing conversation
    files: list[str] = []                  # File UUIDs to make available
    max_steps: int = 10                    # Maximum agent loop iterations
    enable_knowledge_base: bool = True     # Use KB for context
```

**Response (SSE stream):**
```
event: task_created
data: {"task_id": "uuid", "status": "planning"}

event: step
data: {
    "step_number": 1,
    "type": "plan",
    "content": "I'll analyze this task in the following steps:\n1. Extract text from the uploaded PDF...",
    "model_used": "llama3.2:1b"
}

event: step
data: {
    "step_number": 2,
    "type": "act",
    "content": "Calling OCR tool to extract text from the inspection report...",
    "tool_call": {
        "tool_name": "ocr_extract",
        "tool_input": {"file_id": "uuid"},
        "status": "running"
    }
}

event: tool_result
data: {
    "step_number": 2,
    "tool_name": "ocr_extract",
    "tool_output": "Page 1:\nINSPECTION REPORT\nUnit: CDU-2\nDate: 15-Mar-2025...",
    "status": "success",
    "duration_ms": 4200
}

event: step
data: {
    "step_number": 3,
    "type": "observe",
    "content": "The inspection report covers CDU-2 corrosion survey. Key findings:\n1. Thinning at elbow E-204...",
    "model_used": "llama3.2:1b"
}

event: step
data: {
    "step_number": 4,
    "type": "act",
    "content": "Generating Word document with the approval note...",
    "tool_call": {
        "tool_name": "doc_generate",
        "tool_input": {"type": "docx", "template": "approval_note", "data": {...}},
        "status": "running"
    }
}

event: tool_result
data: {
    "step_number": 4,
    "tool_name": "doc_generate",
    "tool_output": "Generated: approval_note_CDU2_2025.docx",
    "file_id": "uuid",
    "status": "success"
}

event: step
data: {
    "step_number": 5,
    "type": "reflect",
    "content": "Task complete. I've extracted findings from the inspection report and generated an approval note.",
    "model_used": "llama3.2:1b"
}

event: done
data: {
    "task_id": "uuid",
    "status": "completed",
    "total_steps": 5,
    "output_files": ["uuid"],
    "result_summary": "Approval note generated for CDU-2 corrosion inspection."
}
```

---

### POST `/api/files/upload`

Upload one or more files.

**Request:** `multipart/form-data`
- `files`: One or more files
- `conversation_id` (optional): Associate with conversation

**Response:**
```python
class FileUploadResponse(msgspec.Struct):
    files: list[UploadedFile]
    
class UploadedFile(msgspec.Struct):
    id: str                 # UUID
    original_name: str
    file_type: str          # "pdf", "image", "docx", "xlsx", "txt", "csv"
    file_size: int          # Bytes
    mime_type: str
```

---

### POST `/api/knowledge/search`

Search the local knowledge base.

**Request:**
```python
class KnowledgeSearchRequest(msgspec.Struct):
    query: str
    top_k: int = 5
    search_type: str = "hybrid"  # "fts" (full-text), "semantic", "hybrid"
```

**Response:**
```python
class KnowledgeSearchResponse(msgspec.Struct):
    results: list[SearchResult]
    query: str
    search_type: str
    
class SearchResult(msgspec.Struct):
    chunk_id: str
    document_id: str
    document_name: str
    content: str            # The chunk text
    score: float            # Relevance score (0-1)
    metadata: dict          # Page number, section, etc.
```

---

### GET `/api/models`

List available models and their status.

**Response:**
```python
class ModelsResponse(msgspec.Struct):
    models: list[ModelInfo]
    
class ModelInfo(msgspec.Struct):
    name: str               # "llama3.2:1b"
    purpose: str            # "General chat and summarization"
    task_types: list[str]   # ["general_chat", "summarization", "document_draft"]
    size_gb: float          # 0.8
    is_loaded: bool         # True if currently in VRAM
    parameters: str         # "1B"
    quantization: str       # "Q4_K_M"
    license: str            # "Llama 3.2 Community License"
```

---

### GET `/api/models/ps`

Check which models are currently loaded in memory.

**Response:**
```python
class ModelPsResponse(msgspec.Struct):
    running: list[RunningModel]
    
class RunningModel(msgspec.Struct):
    name: str
    size_vram: int          # Bytes of VRAM used
    expires_at: str | None  # Null if keep_alive=-1
    processor: str          # "gpu" or "cpu"
```

---

### GET `/api/network/connections`

Live network connections for sovereignty proof.

**Response:**
```python
class NetworkConnectionsResponse(msgspec.Struct):
    connections: list[NetworkConnection]
    total_connections: int
    external_connections: int  # Should always be 0
    timestamp: str
    
class NetworkConnection(msgspec.Struct):
    local_address: str      # "127.0.0.1:8000"
    remote_address: str     # "127.0.0.1:11434"
    protocol: str           # "TCP"
    status: str             # "ESTABLISHED"
    process: str | None     # "python.exe" / "ollama.exe"
    is_local: bool          # True if remote is localhost/LAN
```

---

### GET `/api/health`

System health check.

**Response:**
```python
class HealthResponse(msgspec.Struct):
    status: str             # "healthy" | "degraded" | "unhealthy"
    ollama: ServiceStatus
    database: ServiceStatus
    models: dict[str, bool] # {"llama3.2:1b": True, "qwen2.5-coder:1.5b": True, ...}
    disk_usage_gb: float
    uptime_seconds: int
    version: str            # "1.0.0"
    
class ServiceStatus(msgspec.Struct):
    status: str             # "up" | "down"
    latency_ms: int
    details: str | None = None
```

---

## FastAPI + msgspec Integration

Since FastAPI doesn't natively support msgspec Structs, we implement a thin adapter:

```python
# app/core/msgspec_adapter.py
import msgspec
from fastapi import Response
from fastapi.responses import JSONResponse

class MsgspecJSONResponse(Response):
    """Custom FastAPI response that uses msgspec for JSON encoding."""
    media_type = "application/json"
    
    def __init__(self, content, status_code=200, **kwargs):
        body = msgspec.json.encode(content)
        super().__init__(content=body, status_code=status_code, **kwargs)

# Usage in route handlers:
@router.post("/api/chat")
async def chat(request: Request):
    body = await request.body()
    req = msgspec.json.decode(body, type=ChatRequest)
    # ... process ...
    return MsgspecJSONResponse(response_struct)
```

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

All errors follow a consistent format:

```python
class APIError(msgspec.Struct):
    error: str              # Error type: "validation_error", "model_error", "tool_error"
    detail: str             # Human-readable error message
    status_code: int        # HTTP status code
    request_id: str | None = None
```

| Status Code | Meaning |
|---|---|
| 400 | Invalid request (missing fields, invalid file type) |
| 404 | Conversation / task / file not found |
| 422 | Validation error (msgspec decode failure) |
| 500 | Internal server error (Ollama down, tool crash) |
| 503 | Model not loaded / Ollama unreachable |

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
