# 03 — Solution Architecture

## High-Level Architecture

```
┌────────────────────────────────────────────────────────────────────────────┐
│                        KAVACH AI — Air-Gapped Workbench                    │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    FRONTEND (Next.js 15 + Bun)                      │  │
│   │                                                                     │  │
│   │   Cult UI Components (Shadcn-compatible)                            │  │
│   │   ├── Agent Chat Interface (streaming, multi-turn)                  │  │
│   │   ├── File Upload Panel (PDF, images, documents)                    │  │
│   │   ├── Task Planner View (agent steps, tool calls)                   │  │
│   │   ├── Code Sandbox Output                                           │  │
│   │   ├── Document Preview (generated DOCX/XLSX/PPTX)                   │  │
│   │   ├── Knowledge Base Manager                                        │  │
│   │   └── Network Monitor Dashboard (sovereignty proof)                 │  │
│   │                                                                     │  │
│   │   localhost:3000                                                     │  │
│   └───────────────────────────┬─────────────────────────────────────────┘  │
│                               │ HTTP/JSON + SSE (streaming)                │
│                               ▼                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │                    BACKEND (FastAPI + UV)                            │  │
│   │                                                                     │  │
│   │   ┌──────────────┐  ┌───────────────┐  ┌────────────────────────┐  │  │
│   │   │ Model Router  │  │ Agent Engine  │  │ Tool Registry          │  │  │
│   │   │               │  │               │  │                        │  │  │
│   │   │ Classifies    │  │ Plan → Act →  │  │ • file_read            │  │  │
│   │   │ task type →   │  │ Observe →     │  │ • file_write           │  │  │
│   │   │ picks model:  │  │ Reflect →     │  │ • code_execute         │  │  │
│   │   │               │  │ Repeat        │  │ • doc_generate         │  │  │
│   │   │ chat → llama  │  │               │  │ • spreadsheet_read     │  │  │
│   │   │ code → qwen-  │  │ Max 10 steps  │  │ • knowledge_search     │  │  │
│   │   │       coder   │  │ per task      │  │ • ocr_extract          │  │  │
│   │   │ vision → qwen │  │               │  │ • image_analyze        │  │  │
│   │   │         -vl   │  │               │  │ • web_search (local)   │  │  │
│   │   └──────┬───────┘  └───────┬───────┘  └───────────┬────────────┘  │  │
│   │          │                  │                       │              │  │
│   │   ┌──────▼──────────────────▼───────────────────────▼──────────┐   │  │
│   │   │                    Service Layer                           │   │  │
│   │   │                                                            │   │  │
│   │   │  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │   │  │
│   │   │  │ Ollama SDK   │  │ Code Sandbox │  │ Doc Generator    │  │   │  │
│   │   │  │ (AsyncClient)│  │ (subprocess  │  │ (python-docx,    │  │   │  │
│   │   │  │              │  │  + tempdir)  │  │  openpyxl,       │  │   │  │
│   │   │  │ 3 models     │  │              │  │  python-pptx)    │  │   │  │
│   │   │  │ preloaded    │  │ Timeout: 30s │  │                  │  │   │  │
│   │   │  │ keep_alive   │  │ Memory: 512M │  │                  │  │   │  │
│   │   │  └──────┬───────┘  └──────────────┘  └──────────────────┘  │   │  │
│   │   │         │                                                   │   │  │
│   │   │  ┌──────▼───────┐  ┌──────────────┐                        │   │  │
│   │   │  │ RAG Pipeline  │  │ OCR Engine   │                        │   │  │
│   │   │  │ (local embeds │  │ (Qwen2.5-VL  │                        │   │  │
│   │   │  │  + SQLite FTS)│  │  on-device)  │                        │   │  │
│   │   │  └──────────────┘  └──────────────┘                        │   │  │
│   │   └────────────────────────────────────────────────────────────┘   │  │
│   │                                                                     │  │
│   │   ┌──────────────────────┐  ┌──────────────────────────────────┐   │  │
│   │   │ Tortoise ORM         │  │ Ollama Server                    │   │  │
│   │   │ + SQLite             │  │ localhost:11434                   │   │  │
│   │   │                      │  │                                  │   │  │
│   │   │ • conversations      │  │ Models (preloaded at startup):   │   │  │
│   │   │ • messages           │  │ ├── llama3.2:1b (general chat)   │   │  │
│   │   │ • agent_tasks        │  │ ├── qwen2.5-coder:1.5b (code)   │   │  │
│   │   │ • tool_calls         │  │ └── qwen2.5vl:3b (vision/OCR)   │   │  │
│   │   │ • documents          │  │                                  │   │  │
│   │   │ • knowledge_chunks   │  │ keep_alive = -1 (never unload)   │   │  │
│   │   │ • file_uploads       │  │                                  │   │  │
│   │   └──────────────────────┘  └──────────────────────────────────┘   │  │
│   │                                                                     │  │
│   │   localhost:8000                                                     │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
│                                                                            │
│   ┌─────────────────────────────────────────────────────────────────────┐  │
│   │  NETWORK FIREWALL: ALL OUTBOUND BLOCKED. ZERO EXTERNAL CALLS.      │  │
│   └─────────────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. Frontend (`frontend/`, Next.js 15 App Router + Bun)

**UI Framework:** Cult UI components (Shadcn-compatible, MIT licensed, copy-paste)

- **Routes:**
  - `/` — Dashboard / landing (project info, system status, model health)
  - `/chat` — Primary agent chat interface (streaming, multi-turn, file upload)
  - `/tasks` — Agent task history (view past agentic workflows, steps, outputs)
  - `/knowledge` — Knowledge base manager (upload SOPs, manuals, index status)
  - `/network` — Network monitor (live proof of zero external calls)
  - `/settings` — Model configuration, system preferences

- **Key Components (from Cult UI / custom):**
  - `ChatWindow` — Agent chat with streaming token display
  - `MessageBubble` — User/assistant messages with tool call visualization
  - `FileUploadZone` — Drag-and-drop for PDFs, images, documents
  - `AgentStepView` — Collapsible view of agent planning/execution steps
  - `CodeBlock` — Syntax-highlighted code with "Run in Sandbox" button
  - `DocumentPreview` — Preview generated DOCX/XLSX/PPTX with download
  - `ModelBadge` — Shows which model was auto-selected for each response
  - `NetworkMonitor` — Real-time display of all network connections (proof of air-gap)

- **State Management:** React hooks + SWR for server state
- **Styling:** Tailwind CSS (via Cult UI) + custom theme

### 2. Backend (`backend/`, FastAPI + UV)

#### API Layer (`app/api/`)
- `chat.py` — Chat endpoint (SSE streaming)
- `agent.py` — Agentic task execution endpoint
- `files.py` — File upload/download
- `knowledge.py` — Knowledge base CRUD + search
- `models.py` — Model status, health check
- `network.py` — Network connection logs for sovereignty proof
- `health.py` — System health check

#### Core Services (`app/core/`)
- `config.py` — Configuration via environment variables (msgspec Struct)
- `database.py` — Tortoise ORM initialization with SQLite
- `ollama_client.py` — Ollama AsyncClient wrapper with model preloading

#### Model Router (`app/router/`)
- `classifier.py` — Task type classifier (keyword + heuristic based)
- `router.py` — Maps task type → model selection

```python
# Router logic (simplified)
ROUTING_TABLE = {
    TaskType.GENERAL_CHAT:    "llama3.2:1b",
    TaskType.CODE_GENERATION: "qwen2.5-coder:1.5b",
    TaskType.CODE_REVIEW:     "qwen2.5-coder:1.5b",
    TaskType.CODE_DEBUG:      "qwen2.5-coder:1.5b",
    TaskType.VISION:          "qwen2.5vl:3b",
    TaskType.OCR:             "qwen2.5vl:3b",
    TaskType.DOCUMENT_ANALYSIS: "qwen2.5vl:3b",
    TaskType.SUMMARIZATION:   "llama3.2:1b",
    TaskType.DOCUMENT_DRAFT:  "llama3.2:1b",
}
```

#### Agent Engine (`app/agent/`)
- `planner.py` — Decomposes user request into steps
- `executor.py` — Executes steps with tool calls
- `observer.py` — Checks tool output, decides next action
- `loop.py` — Main ReAct loop (Plan → Act → Observe → Reflect)

#### Tool Registry (`app/tools/` + `app/rag/`)
The planner emits these canonical names; aliases were removed.

- `file_read` — Read files from workspace
- `file_write` — Write files to workspace
- `code_execute` — Sandboxed Python execution (subprocess + tempdir)
- `generate_word_document` — DOCX via `python-docx`
- `generate_excel_sheet` — XLSX via `openpyxl`
- `generate_presentation` — PPTX via `python-pptx`
- `search_knowledge_base` — Hybrid FTS5 + vector search via SQLite (RRF merge)
- `extract_text_from_image` — OCR pass on an attached image via Qwen2.5-VL
- `analyze_engineering_diagram` — P&ID / drawing interpretation via Qwen2.5-VL

#### RAG Pipeline (`app/rag/`)
- `chunker.py` — Document chunking (recursive text splitter)
- `embedder.py` — Local embeddings via Ollama embed API
- `retriever.py` — SQLite FTS5 full-text search + semantic similarity
- `pipeline.py` — Orchestrates chunk → embed → store → retrieve → generate

#### Schemas (`app/schemas/`)
- **Request bodies** use Pydantic `BaseModel` (FastAPI wires validation natively)
- **Response payloads** use plain dicts; the hot-path file-metadata responses use `msgspec.json.encode` inside `app/api/files.py:_msgspec_response` for ~10x faster serialization
- See `docs/04_TECH_STACK.md` for the rationale

### 3. Data Layer (Tortoise ORM + SQLite)

**Why SQLite (not Postgres):**
- Zero setup — just a file. Perfect for on-premise single-server deployment.
- FTS5 extension provides full-text search (replaces need for Elasticsearch)
- Tortoise ORM provides async access
- No additional service to install/manage on the org's server

### 4. AI Layer (Ollama)

**Model Preloading Strategy:**

```python
# At backend startup (lifespan event)
async def preload_models():
    client = AsyncClient(host="http://localhost:11434")
    
    models = ["llama3.2:1b", "qwen2.5-coder:1.5b", "qwen2.5vl:3b"]
    
    for model in models:
        # Pull if not already downloaded
        await client.pull(model)
        
        # Warm up: send a dummy request with keep_alive=-1 (never unload)
        await client.chat(
            model=model,
            messages=[{"role": "user", "content": "hello"}],
            keep_alive=-1  # Keep in VRAM forever
        )
    
    # Verify all models are loaded
    ps_result = await client.ps()
    # Should show all 3 models in memory
```

**Memory Requirements (estimated):**
| Model | Parameters | Quantization | VRAM Required |
|---|---|---|---|
| llama3.2:1b | 1B | Q4_K_M | ~0.8 GB |
| qwen2.5-coder:1.5b | 1.5B | Q4_K_M | ~1.1 GB |
| qwen2.5vl:3b | 3B | Q4_K_M | ~2.2 GB |
| **Total** | | | **~4.1 GB** |

> This fits comfortably on a single GPU with 6+ GB VRAM (RTX 3060 or better), or in RAM with CPU inference.

## Request Flow

### Standard Chat Flow
```
1. User types message in /chat
2. Frontend POST /api/chat {message, conversation_id, files[]}
3. Backend:
   a. Model Router classifies task type from message content
   b. Selects appropriate model (e.g., "llama3.2:1b" for general chat)
   c. Retrieves conversation history from SQLite
   d. If knowledge base enabled, RAG pipeline retrieves relevant chunks
   e. Constructs prompt with system message + context + history + user message
   f. Streams response from Ollama via SSE
   g. Saves message + response to SQLite
4. Frontend renders streamed tokens + model badge
```

### Agentic Task Flow
```
1. User describes complex task: "Read this inspection report and draft an approval note"
2. Frontend POST /api/agent/execute {task_description, files[], max_steps: 10}
3. Backend Agent Loop:
   Step 1 (Plan):
     - LLM analyzes task → produces plan: ["extract text from PDF", "identify findings", "draft approval note", "generate Word doc"]
   Step 2 (Act):
     - Tool call: ocr_extract(file="inspection_report.pdf")
     - Tool returns: extracted text from all pages
   Step 3 (Observe):
     - LLM reviews extracted text → identifies key findings, defects, recommendations
   Step 4 (Act):
     - Tool call: knowledge_search(query="approval note template MRPL format")
     - Tool returns: relevant SOP sections
   Step 5 (Act):
     - Tool call: doc_generate(type="docx", content=formatted_approval_note)
     - Tool returns: path to generated .docx file
   Step 6 (Reflect):
     - LLM reviews output → confirms completeness → terminates
4. Frontend shows each step in AgentStepView + final document download
```

## Deployment Topology

### Single Server (target for SIH demo + production)
```
┌──────────────────────────────────────────┐
│          Organization's Server            │
│                                          │
│  ┌──────────────┐  ┌──────────────────┐  │
│  │  Ollama       │  │  Backend         │  │
│  │  (GPU server) │  │  (FastAPI + UV)  │  │
│  │  :11434       │  │  :8000           │  │
│  └──────────────┘  └──────────────────┘  │
│                                          │
│  ┌──────────────┐  ┌──────────────────┐  │
│  │  Frontend     │  │  SQLite DB       │  │
│  │  (Next.js)    │  │  (file on disk)  │  │
│  │  :3000        │  │                  │  │
│  └──────────────┘  └──────────────────┘  │
│                                          │
│  🔒 Firewall: ALL outbound BLOCKED       │
└──────────────────────────────────────────┘
```

### Development (hackathon)
- `bun run dev` for frontend (hot reload)
- `uv run uvicorn app.main:app --reload` for backend
- `ollama serve` for model serving
- All on a single laptop/workstation with mid-range GPU

## Security Architecture

### Air-Gap Proof
1. **Firewall rules** — iptables/Windows Firewall blocking all outbound on the demo machine
2. **Network monitor endpoint** — `/api/network/connections` returns live `netstat` output
3. **Frontend dashboard** — Real-time display of all active network connections
4. **Ollama configured for local only** — `OLLAMA_HOST=127.0.0.1:11434`
5. **No external dependencies at runtime** — All models pre-downloaded, all packages vendored

### Data Handling
- All data stored locally in SQLite database
- File uploads stored in local `./data/uploads/` directory
- Generated documents in `./data/outputs/`
- Knowledge base in `./data/knowledge/`
- No telemetry, no analytics, no external logging
