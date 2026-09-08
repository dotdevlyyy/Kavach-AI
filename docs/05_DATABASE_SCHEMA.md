# 05 — Database Schema

> **ORM:** Tortoise ORM with SQLite + FTS5
> **Schema Definitions:** Tortoise Model classes
> **Migrations:** none — `Tortoise.generate_schemas()` runs at startup (drop the DB file to reset)

## Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────────┐
│  Conversation    │       │  Message                 │
│─────────────────│       │─────────────────────────│
│  id (UUID, PK)   │◄──┐  │  id (UUID, PK)           │
│  title            │   │  │  conversation_id (FK)    │
│  created_at       │   └──│  role (user/assistant/    │
│  updated_at       │      │        system/tool)      │
│  model_override   │      │  content                 │
│  system_prompt    │      │  model_used              │
└─────────────────┘      │  task_type               │
└─────────────────┘      │  tokens_in               │
                          │  tokens_out              │
                          │  latency_ms              │
                          │  files (JSON)            │
                          │  created_at              │
                          └──────┬──────────────────┘
                                 │
                                 │ 1:N
                                 ▼
                          ┌─────────────────────────┐
                          │  ToolCall                 │
                          │─────────────────────────│
                          │  id (UUID, PK)           │
                          │  message_id (FK)         │
                          │  agent_task_id (FK, opt) │
                          │  tool_name               │
                          │  tool_input (JSON)       │
                          │  tool_output (TEXT)      │
                          │  status (enum)           │
                          │  duration_ms             │
                          │  created_at              │
                          └─────────────────────────┘

┌─────────────────────────┐       ┌─────────────────────────┐
│  AgentTask               │       │  AgentStep               │
│─────────────────────────│       │─────────────────────────│
│  id (UUID, PK)           │◄──┐  │  id (UUID, PK)           │
│  conversation_id (FK)    │   │  │  agent_task_id (FK)      │
│  description             │   └──│  step_number             │
│  status (enum)           │      │  type (plan/act/observe/ │
│  result_summary          │      │        reflect)          │
│  output_files (JSON)     │      │  content                 │
│  total_steps             │      │  model_used              │
│  max_steps               │      │  duration_ms             │
│  created_at              │      │  created_at              │
│  completed_at            │      └─────────────────────────┘
└─────────────────────────┘      └─────────────────────────┘

┌─────────────────────────┐       ┌─────────────────────────┐
│  Document                │       │  KnowledgeChunk          │
│─────────────────────────│       │─────────────────────────│
│  id (UUID, PK)           │◄──┐  │  id (UUID, PK)           │
│  filename                │   │  │  document_id (FK)        │
│  original_name           │   └──│  chunk_index             │
│  file_path               │      │  content                 │
│  file_type               │      │  embedding (BLOB)        │
│  file_size               │      │  metadata (JSON)         │
│  mime_type               │      │  created_at              │
│  is_knowledge_base       │      └─────────────────────────┘
│  created_at              │      ┌─────────────────────────┐
└─────────────────────────┘      │  NetworkLog              │
                                  │─────────────────────────│
                                  │  id (INT, PK, auto)      │
┌─────────────────────────┐      │  timestamp               │
│  FileUpload              │      │  local_addr              │
│─────────────────────────│      │  remote_addr             │
│  id (UUID, PK)           │      │  protocol                │
│  conversation_id (FK,opt)│      │  status                  │
│  original_name           │      │  process_name            │
│  stored_path             │      │  is_local (BOOL)         │
│  file_type               │      └─────────────────────────┘
│  file_size               │
│  uploaded_at             │
└─────────────────────────┘
```

## Tortoise ORM Model Definitions

### Conversation

```python
from tortoise import fields, models
import uuid

class Conversation(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    title = fields.CharField(max_length=500, default="New Conversation")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    model_override = fields.CharField(max_length=100, null=True)  # Force specific model
    system_prompt = fields.TextField(null=True)

    messages: fields.ReverseRelation["Message"]
    agent_tasks: fields.ReverseRelation["AgentTask"]
    
    class Meta:
        table = "conversations"
        ordering = ["-updated_at"]
```

### Message

```python
class Message(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation", related_name="messages", on_delete=fields.CASCADE
    )
    role = fields.CharField(max_length=20)  # free-form string: "user" | "assistant" | "system" | "tool"
    content = fields.TextField()
    model_used = fields.CharField(max_length=100, null=True)
    task_type = fields.CharField(max_length=50, null=True)  # "general_chat", "code", "vision"
    tokens_in = fields.IntField(default=0)
    tokens_out = fields.IntField(default=0)
    latency_ms = fields.IntField(default=0)
    files = fields.JSONField(default=list)  # List of file UUIDs attached
    created_at = fields.DatetimeField(auto_now_add=True)
    
    tool_calls: fields.ReverseRelation["ToolCall"]
    
    class Meta:
        table = "messages"
        ordering = ["created_at"]
```

### ToolCall

```python
class ToolCall(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    message = fields.ForeignKeyField(
        "models.Message", related_name="tool_calls", on_delete=fields.SET_NULL, null=True
    )
    agent_task = fields.ForeignKeyField(
        "models.AgentTask", related_name="tool_calls",
        on_delete=fields.SET_NULL, null=True
    )
    tool_name = fields.CharField(max_length=100)  # "code_execute", "file_read", etc.
    tool_input = fields.JSONField(default=dict)
    tool_output = fields.TextField(default="")
    status = fields.CharEnumField(
        enum_type=ToolCallStatus,  # "pending", "running", "success", "error"
        max_length=20, default="pending"
    )
    duration_ms = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "tool_calls"
        ordering = ["created_at"]
```

### AgentTask

```python
class AgentTask(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation", related_name="agent_tasks", on_delete=fields.CASCADE
    )
    description = fields.TextField()
    status = fields.CharEnumField(
        enum_type=AgentTaskStatus,  # "planning", "executing", "completed", "failed", "cancelled"
        max_length=20, default="planning"
    )
    result_summary = fields.TextField(null=True)
    output_files = fields.JSONField(default=list)  # List of generated file paths
    total_steps = fields.IntField(default=0)
    max_steps = fields.IntField(default=10)
    created_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)
    
    steps: fields.ReverseRelation["AgentStep"]
    
    class Meta:
        table = "agent_tasks"
        ordering = ["-created_at"]
```

### AgentStep

```python
class AgentStep(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    agent_task = fields.ForeignKeyField(
        "models.AgentTask", related_name="steps", on_delete=fields.CASCADE
    )
    step_number = fields.IntField()
    type = fields.CharEnumField(
        enum_type=StepType,  # "plan", "act", "observe", "reflect"
        max_length=20
    )
    content = fields.TextField()  # LLM reasoning / observation text
    model_used = fields.CharField(max_length=100, null=True)
    duration_ms = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "agent_steps"
        ordering = ["step_number"]
```

### Document

```python
class Document(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    filename = fields.CharField(max_length=500)  # Stored filename (UUID-based)
    original_name = fields.CharField(max_length=500)  # User's original filename
    file_path = fields.CharField(max_length=1000)  # Full path on disk
    file_type = fields.CharField(max_length=50)  # "pdf", "image", "docx", "xlsx"
    file_size = fields.IntField()  # Bytes
    mime_type = fields.CharField(max_length=200)
    is_knowledge_base = fields.BooleanField(default=False)  # Part of KB?
    created_at = fields.DatetimeField(auto_now_add=True)
    
    chunks: fields.ReverseRelation["KnowledgeChunk"]
    
    class Meta:
        table = "documents"
        ordering = ["-created_at"]
```

### KnowledgeChunk

```python
class KnowledgeChunk(models.Model):
    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    document = fields.ForeignKeyField(
        "models.Document", related_name="chunks", on_delete=fields.CASCADE
    )
    chunk_index = fields.IntField()
    content = fields.TextField()  # The chunk text
    embedding = fields.BinaryField(null=True)  # Serialized float32 array
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "knowledge_chunks"
        ordering = ["chunk_index"]
```

### NetworkLog

```python
class NetworkLog(models.Model):
    id = fields.IntField(pk=True)  # Auto-increment
    timestamp = fields.DatetimeField(auto_now_add=True)
    local_addr = fields.CharField(max_length=100)
    remote_addr = fields.CharField(max_length=100)
    protocol = fields.CharField(max_length=10)  # "TCP", "UDP"
    status = fields.CharField(max_length=50)  # "ESTABLISHED", "LISTEN", etc.
    process_name = fields.CharField(max_length=200, null=True)
    is_local = fields.BooleanField(default=True)  # Is remote addr local?
    
    class Meta:
        table = "network_logs"
        ordering = ["-timestamp"]
```

## SQLite FTS5 (Full-Text Search)

For knowledge base search, we create a virtual FTS5 table:

```sql
-- Created via raw SQL in database initialization
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    chunk_id,
    content,
    document_name,
    tokenize='porter unicode61'
);
```

Rows are populated explicitly by `app/rag/pipeline.py:ingest_document` and removed explicitly by `app/api/knowledge.py:delete_document`. No triggers — schema and Python code stay decoupled.

## Enums

```python
import enum

class TaskType(str, enum.Enum):
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_DEBUG = "code_debug"
    VISION = "vision"
    OCR = "ocr"
    DOCUMENT_ANALYSIS = "document_analysis"
    SUMMARIZATION = "summarization"
    DOCUMENT_DRAFT = "document_draft"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"

class ToolCallStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"

class AgentTaskStatus(str, enum.Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepType(str, enum.Enum):
    PLAN = "plan"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"
```

`Message.role` is a free-form `CharField` (no enum); tool status / task status / step type are all `CharEnumField`.

## Tortoise ORM Configuration

```python
# app/core/database.py
TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": "./data/kavach.db",
                "journal_mode": "WAL",  # Write-Ahead Logging for better concurrency
            },
        }
    },
    "apps": {
        "models": {
            "models": [
                "app.models.conversation",
                "app.models.message",
                "app.models.tool_call",
                "app.models.agent_task",
                "app.models.agent_step",
                "app.models.document",
                "app.models.knowledge_chunk",
                "app.models.file_upload",
                "app.models.network_log",
            ],
            "default_connection": "default",
        },
    },
}
```

## Database Size Estimates

| Table | Rows (after 1 month heavy use) | Estimated Size |
|---|---|---|
| conversations | ~500 | < 1 MB |
| messages | ~10,000 | ~5 MB |
| tool_calls | ~5,000 | ~3 MB |
| agent_tasks | ~200 | < 1 MB |
| agent_steps | ~2,000 | ~2 MB |
| documents | ~500 | < 1 MB |
| knowledge_chunks | ~50,000 | ~50 MB |
| knowledge_fts | ~50,000 | ~30 MB |
| network_logs | ~100,000 | ~20 MB |
| **Total** | | **~112 MB** |

SQLite handles this trivially. The entire database fits in RAM.
