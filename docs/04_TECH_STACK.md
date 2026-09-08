# 04 — Tech Stack

> Every component is open-source (MIT/Apache 2.0). Zero cloud dependencies. Zero license fees.

## Frontend

### Next.js 15 (App Router) — `15.x`

- **Role:** Full-stack React framework for the agent UI
- **Why:** App Router for nested layouts, RSC for fast first paint, built-in SSE support for streaming AI responses, API routes for BFF pattern
- **Runtime:** **Bun** (not Node.js) — 4x faster install, 3x faster runtime, built-in TypeScript
- **Alternatives rejected:**
  - Vite + React: No SSR, more boilerplate for routing
  - Remix: Smaller ecosystem, no clear advantage for chat UI
  - SvelteKit: Team unfamiliar

### Cult UI — latest (copy-paste components)

- **Role:** Agent/Chat UI component library
- **Source:** https://www.cult-ui.com/ (MIT licensed, 6.1k GitHub stars)
- **Why:** Pre-built agent chat patterns, shadcn-compatible, designed for AI interfaces. Has:
  - Multi-step tool pattern components
  - Evaluator-optimizer pattern components
  - Orchestrator pattern components
  - Routing pattern components
- **How used:** Copy-paste the components we need, customize for our use case. Not installed as npm dependency — source code owned by us.
- **Alternatives rejected:**
  - shadcn/ui alone: No AI/agent-specific patterns
  - Vercel AI SDK UI: Requires Vercel AI SDK backend (cloud-oriented)
  - Custom from scratch: 10-day hackathon — can't afford it

### Tailwind CSS — `3.4+`

- **Role:** Utility-first styling (comes with Cult UI)
- **Why:** Cult UI is built on Tailwind + shadcn. Using Tailwind is mandatory for compatibility.
- **Alternatives rejected:**
  - Vanilla CSS: Incompatible with Cult UI component patterns
  - CSS Modules: More files, slower iteration

### TypeScript — `5.5+`

- **Role:** Type safety for frontend code
- **Why:** Required by Cult UI and shadcn. Catches bugs early in a hackathon.

### Lucide React — `0.400+`

- **Role:** Icon library (used by Cult UI / shadcn)
- **Why:** Tree-shakeable, consistent style, already a dependency of shadcn components

## Backend

### FastAPI — `0.115+`

- **Role:** Async API server, request validation, SSE streaming, OpenAPI docs
- **Why:** Async-native (critical for Ollama streaming), automatic OpenAPI at `/docs`, middleware support for CORS/logging
- **Alternatives rejected:**
  - Flask: No native async
  - Django: Too heavy, ORM lock-in
  - Express (Node): Team is Python-first

### msgspec — `0.19+`

- **Role:** Fast serialization of structured payloads (response Structs, embeddings, KB search results).
- **Why chosen over Pydantic for hot paths:**

| Feature | msgspec | Pydantic v2 |
|---|---|---|
| Serialization speed | **10-50x faster** | Baseline |
| Memory usage | **~3x less** | Baseline |
| Struct size | Smaller (C extension) | Larger |
| JSON encode/decode | Built-in, zero-copy | Via json module |

- **Where each is used:**
  - **Pydantic `BaseModel`** — request bodies (`app/schemas/{chat,agent,files}.py`). FastAPI wires validation natively.
  - **msgspec `json.encode`** — selective hot-path JSON encoding inside `app/api/files.py:_msgspec_response`. Response payloads elsewhere are plain dicts.
- **Why both:** request validation is on the cold path (Pydantic wins on ergonomics); JSON encode for the few high-traffic metadata responses saves a few microseconds each.

```python
# app/schemas/chat.py
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str
    conversation_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    model_override: str | None = None
    system_prompt: str | None = None
    enable_knowledge_base: bool = True
```

```python
# app/schemas/agent.py — agent endpoint schema; KB access via `search_knowledge_base` tool.
class AgentExecuteRequest(BaseModel):
    task_description: str
    conversation_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    model_override: str | None = None
    system_prompt: str | None = None
    max_steps: int = 10
```

### Tortoise ORM — `0.22+`

- **Role:** Async ORM for SQLite database access
- **Why chosen over SQLAlchemy:**
  - **Async-native** — designed for asyncio from the ground up
  - **Django-style models** — familiar, readable, less boilerplate
  - **SQLite first-class support** — uses aiosqlite under the hood
  - **Built-in migrations** via Aerich
- **Alternatives rejected:**
  - SQLAlchemy 2.0 + asyncio: More boilerplate, ORM pattern is heavier
  - Raw aiosqlite: No ORM, manual SQL everywhere
  - Peewee: No async support

### SQLite — `3.45+` (with FTS5)

- **Role:** Primary data store for conversations, messages, tasks, knowledge base
- **Why chosen over PostgreSQL:**
  - **Zero setup** — just a file. Critical for on-premise deployment simplicity.
  - **No extra service** — no Docker, no port, no auth to manage
  - **FTS5** — built-in full-text search, replaces need for Elasticsearch
  - **WAL mode** — concurrent reads with single-writer; sufficient for single-server deployment
  - **Backup** — just copy the file
- **When to upgrade to Postgres:** Only if multi-server / multi-user concurrent writes become a requirement (post-hackathon)

### UV — `0.4+`

- **Role:** Python package manager and virtualenv tool
- **Why chosen over pip:**
  - **10-100x faster** dependency resolution and installation
  - **Built-in virtualenv** management
  - **Lockfile support** — reproducible installs on the org's server
  - **Rust-based** — single binary, no bootstrap dependency
- **Usage:**
  ```bash
  uv init backend
  uv add fastapi uvicorn msgspec tortoise-orm aiosqlite ollama python-docx openpyxl python-pptx
  uv run uvicorn app.main:app --reload
  ```

### Ollama Python SDK — `0.4+`

- **Role:** Interface to local Ollama server for all LLM operations
- **Why:** Official SDK, supports:
  - `chat()` — conversational generation
  - `generate()` — single-prompt generation
  - `embed()` — embedding generation for RAG
  - `pull()` — model downloading (at startup)
  - `ps()` — check which models are loaded in memory
  - `AsyncClient` — full async support for FastAPI
  - `stream=True` — token-by-token streaming
  - `keep_alive=-1` — keep model in VRAM forever (critical for instant switching)

### Models via Ollama

| Model | Purpose | Size | VRAM | License |
|---|---|---|---|---|
| `llama3.2:1b` | General chat, summarization, document drafting | 1B params | ~0.8 GB | Llama 3.2 Community License |
| `qwen2.5-coder:1.5b` | Code generation, code review, debugging | 1.5B params | ~1.1 GB | Apache 2.0 |
| `qwen2.5vl:3b` | Vision, OCR, image analysis, scanned document understanding | 3B params | ~2.2 GB | Apache 2.0 |

**Total VRAM for all 3 models simultaneously: ~4.1 GB**

### Additional Python Libraries

| Library | Version | Purpose |
|---|---|---|
| `python-docx` | 1.1+ | Generate Word documents + parse DOCX for KB |
| `openpyxl` | 3.1+ | Generate/read Excel files |
| `python-pptx` | 1.0+ | Generate PowerPoint presentations |
| `uvicorn` | 0.30+ | ASGI server for FastAPI |
| `aiosqlite` | 0.20+ | Async SQLite driver (Tortoise ORM backend) |
| `loguru` | 0.7+ | Structured logging |
| `python-multipart` | 0.0.9+ | File upload handling in FastAPI |
| `psutil` | 5.9+ | Network connection enumeration for sovereignty proof |
| `PyMuPDF` (fitz) | 1.25+ | PDF text extraction (text-based PDFs) |

## DevOps

### Bun — `1.1+`

- **Role:** JavaScript runtime and package manager for frontend
- **Why over Node.js + npm:**
  - **4x faster** package installs
  - **3x faster** runtime execution
  - **Built-in TypeScript** — no transpilation step
  - **Single binary** — easier to install on org's server
- **Usage:**
  ```bash
  bun create next-app frontend
  bun install
  bun run dev
  ```

### Ruff — `0.6+`

- **Role:** Python linter + formatter (replaces flake8, black, isort)
- **Why:** 100x faster than alternatives, single tool, single config

### ESLint + Prettier — `9+ / 3+`

- **Role:** Frontend linting and formatting
- **Why:** Standard for Next.js/TypeScript projects

## Monorepo Structure

```
kavach-ai/
├── frontend/                  # Next.js 15 + Bun
│   ├── app/                   # App Router pages
│   │   ├── layout.tsx
│   │   ├── page.tsx           # Dashboard
│   │   ├── chat/
│   │   │   └── page.tsx       # Agent chat
│   │   ├── tasks/
│   │   │   └── page.tsx       # Task history
│   │   ├── knowledge/
│   │   │   └── page.tsx       # KB manager
│   │   ├── network/
│   │   │   └── page.tsx       # Network monitor
│   │   └── settings/
│   │       └── page.tsx       # Settings
│   ├── components/
│   │   ├── ui/                # Cult UI / shadcn components
│   │   ├── chat/              # Chat-specific components
│   │   ├── agent/             # Agent step visualization
│   │   └── shared/            # Layout, nav, etc.
│   ├── lib/                   # Utilities, API client, types
│   ├── public/                # Static assets
│   ├── bun.lockb
│   ├── package.json
│   ├── next.config.ts
│   ├── tailwind.config.ts
│   └── tsconfig.json
│
├── backend/                   # FastAPI + UV
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app + lifespan (model preload)
│   │   ├── api/               # Route handlers
│   │   │   ├── chat.py
│   │   │   ├── agent.py
│   │   │   ├── files.py
│   │   │   ├── knowledge.py
│   │   │   ├── models.py
│   │   │   ├── network.py
│   │   │   └── health.py
│   │   ├── core/              # Configuration, DB, Ollama client
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── ollama_client.py
│   │   ├── router/            # Model auto-selection
│   │   │   ├── classifier.py
│   │   │   └── router.py
│   │   ├── agent/             # Agentic execution engine
│   │   │   ├── planner.py
│   │   │   ├── executor.py
│   │   │   ├── observer.py
│   │   │   └── loop.py
│   │   ├── tools/             # Tool implementations
│   │   │   ├── registry.py
│   │   │   ├── file_read.py
│   │   │   ├── file_write.py
│   │   │   ├── code_execute.py
│   │   │   ├── doc_generate.py
│   │   │   ├── knowledge_search.py
│   │   │   ├── ocr_extract.py
│   │   │   └── image_analyze.py
│   │   ├── rag/               # RAG pipeline
│   │   │   ├── chunker.py
│   │   │   ├── embedder.py
│   │   │   ├── retriever.py
│   │   │   └── pipeline.py
│   │   ├── schemas/           # Pydantic request bodies; msgspec for hot-path responses
│   │   │   ├── chat.py
│   │   │   ├── agent.py
│   │   │   ├── files.py
│   │   │   └── common.py
│   │   └── models/            # Tortoise ORM models
│   │       ├── conversation.py
│   │       ├── message.py
│   │       ├── agent_task.py
│   │       ├── tool_call.py
│   │       ├── document.py
│   │       └── knowledge_chunk.py
│   ├── data/                  # Local data storage
│   │   ├── uploads/           # User-uploaded files
│   │   ├── outputs/           # Generated documents
│   │   ├── knowledge/         # Knowledge base files
│   │   └── kavach.db          # SQLite database
│   ├── pyproject.toml         # UV project config
│   └── uv.lock               # Locked dependencies
│
├── scripts/                   # Setup and utility scripts
│   ├── setup.sh               # Full setup (install Ollama + pull models)
│   ├── setup.ps1              # Windows setup script
│   └── demo_data.py           # Load sample data for demo
│
├── samples/                   # Sample files for demo
│   ├── inspection_report.pdf  # Sample scanned inspection report
│   ├── pid_drawing.png        # Sample P&ID drawing
│   ├── handwritten_notes.jpg  # Sample handwritten notes
│   └── financial_data.xlsx    # Sample Excel data
│
├── README.md
├── .gitignore
└── LICENSE                    # MIT
```

## Why This Stack Wins

1. **Zero cloud dependencies** — SQLite file, Ollama local, UV vendored packages
2. **Single-server deployable** — No Docker, no Postgres, no Redis, no Kubernetes
3. **4.1 GB total VRAM** — Runs on any mid-range GPU (RTX 3060 or even CPU-only)
4. **msgspec > Pydantic** — 10x faster serialization, lower memory in constrained environments
5. **Bun > npm** — 4x faster installs, faster dev server, built-in TypeScript
6. **UV > pip** — 100x faster installs, reproducible lockfile
7. **Cult UI** — Pre-built agent chat patterns, days saved on frontend
8. **Tortoise ORM + SQLite** — Zero-config database, async-native, FTS5 for search
