# 🛡️ Kavach AI — Master 6-Member Team TODO & Work Allocation

> **Project:** Kavach AI (Air-Gapped Agentic AI Workbench for PSUs & Critical Infrastructure)  
> **Problem Statement ID:** 26117 | **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Team Roster:**  
> - 🌟 **Main Developers (Full Devs):** **ANKIT**, **AMIT**, **PRAGYAN**  
> - 🚀 **AI-Assisted Developers (Beginners):** **RAHUL**, **BASUDEV**, **PRITAM**  

---

## 👥 Team Matrix & Ownership Map

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              KAVACH AI — 6-MEMBER TEAM MATRIX                                          │
├──────────────────────────┬──────────────────────────┬──────────────────────────┬───────────────────────────────────────┤
│ 🌟 ANKIT (Main Dev)      │ 🌟 AMIT (Main Dev)       │ 🌟 PRAGYAN (Main Dev)    │ 🚀 BEGINNER DEVELOPERS (AI-GUIDED)    │
│ Team Lead & Core AI      │ Backend & Deliverables   │ Frontend Lead & Chat UX  │ Specific isolated modules with        │
│                          │                          │                          │ clear input/output contracts:         │
│ • Ollama Model Lifecycle │ • Tortoise ORM + SQLite  │ • Next.js 15 + Cult UI   │                                       │
│ • Heuristic Model Router │ • msgspec Serialization  │ • SSE Stream Consumer    │ 🚀 RAHUL: Document Parsing & Datasets │
│ • ReAct Agent Planner    │ • File Upload / Storage  │ • Interactive Chat Page  │ 🚀 BASUDEV: Local Embeddings & RAG    │
│ • Execution & Reflection │ • Tool Registry Base     │ • Agent Step Visualizer  │ 🚀 PRITAM: Network Audit & UI Pages   │
│ • Sandboxed Code Runner  │ • Word/Excel Deliverables│ • Deliverable Download   │                                       │
│ • Chat & Agent SSE APIs  │ • OCR & Vision Wrapper   │ • Layout & UI Themes     │                                       │
└──────────────────────────┴──────────────────────────┴──────────────────────────┴───────────────────────────────────────┘
```

---

# 🌟 PART 1: MAIN DEVELOPERS (FULL DEVS)

---

## 🧑‍💻 ANKIT — Team Lead & AI Agent Core Architect

> **Primary Focus:** Model orchestration in GPU memory, multi-model auto-selection router, autonomous ReAct agent engine with self-correction, code sandbox, and core SSE endpoints.

### 📁 Files Owned by Ankit
* `backend/app/core/ollama_client.py`
* `backend/app/router/classifier.py`
* `backend/app/router/router.py`
* `backend/app/agent/planner.py`
* `backend/app/agent/executor.py`
* `backend/app/agent/observer.py`
* `backend/app/agent/loop.py`
* `backend/app/tools/code_execute.py`
* `backend/app/api/chat.py`
* `backend/app/api/agent.py`

### 📋 Ankit's Checklist
- [ ] **Repository Setup & Governance:**
  - [ ] Initialize monorepo structure (`backend/`, `frontend/`, `samples/`).
  - [ ] Configure Python `uv` package manager and lockfile.
  - [ ] Verify local Ollama server and test pull of all 3 models (`llama3.2:1b`, `qwen2.5-coder:1.5b`, `qwen2.5vl:3b`).
- [ ] **Ollama Client & GPU Hot-Swap (`ollama_client.py`):**
  - [ ] Build async wrapper around `ollama.AsyncClient`.
  - [ ] Write startup preloading routine with `keep_alive=-1` to lock all 3 models in GPU memory (~4.1 GB total VRAM).
- [ ] **Model Auto-Selection Router (`classifier.py` & `router.py`):**
  - [ ] Implement heuristic keyword + attachment classifier:
    - [ ] If images or P&ID diagrams attached ➔ `qwen2.5vl:3b`
    - [ ] If scanned PDF and OCR keywords present ➔ `qwen2.5vl:3b`
    - [ ] If programming keywords or code blocks present ➔ `qwen2.5-coder:1.5b`
    - [ ] Default / General chat / Summaries ➔ `llama3.2:1b`
  - [ ] Support explicit user override flag (`model_override`).
- [ ] **Autonomous ReAct Agent Loop (`app/agent/`):**
  - [ ] `planner.py`: Generate structured step plan using local LLM.
  - [ ] `executor.py`: Dispatch steps to Amit's Tool Registry.
  - [ ] `observer.py`: Inspect tool outputs and detect errors.
  - [ ] `loop.py`: Run Plan ➔ Act ➔ Observe ➔ Reflect loop with 10-step limit and error self-correction.
- [ ] **Sandboxed Code Runner (`code_execute.py`):**
  - [ ] Secure `asyncio.create_subprocess_exec` runner with 30s timeout, memory limit, and stdout/stderr capture.
- [ ] **Streaming API Handlers:**
  - [ ] `POST /api/chat`: SSE token streaming with metadata event.
  - [ ] `POST /api/agent/execute`: SSE step-by-step progress streaming.

---

## 🧑‍💻 AMIT — Backend Systems, Database & Deliverables Engine

> **Primary Focus:** Database models, SQLite WAL configuration, msgspec schemas & adapter, file upload/download service, tool registry, and concrete deliverable generators (Word, Excel, PowerPoint).

### 📁 Files Owned by Amit
* `backend/app/core/database.py`
* `backend/app/core/msgspec_adapter.py`
* `backend/app/models/*.py` (`conversation.py`, `message.py`, `agent_task.py`, `agent_step.py`, `tool_call.py`, `document.py`, `file_upload.py`)
* `backend/app/schemas/*.py` (`chat.py`, `agent.py`, `files.py`, `common.py`)
* `backend/app/api/files.py`
* `backend/app/tools/registry.py`
* `backend/app/tools/file_read.py` & `backend/app/tools/file_write.py`
* `backend/app/tools/doc_generate.py`
* `backend/app/tools/ocr_extract.py` & `backend/app/tools/image_analyze.py`

### 📋 Amit's Checklist
- [ ] **Database & ORM Setup (`database.py` & `models/`):**
  - [ ] Configure Tortoise ORM with `aiosqlite` targeting `backend/data/kavach.db`.
  - [ ] Enable SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
  - [ ] Implement all Tortoise models: `Conversation`, `Message`, `AgentTask`, `AgentStep`, `ToolCall`, `Document`, `FileUpload`.
- [ ] **msgspec Performance Layer (`schemas/` & `msgspec_adapter.py`):**
  - [ ] Define strict request/response structs for Chat, Agent, Files, and Models.
  - [ ] Implement custom `MsgspecJSONResponse` for FastAPI for 10-50x faster serialization.
- [ ] **File Storage & Upload API (`api/files.py`):**
  - [ ] Setup storage folders: `backend/data/uploads/` and `backend/data/outputs/`.
  - [ ] Build `POST /api/files/upload` (multipart) returning UUID and file metadata.
  - [ ] Build `GET /api/files/{id}` and `GET /api/files/download/{filename}`.
- [ ] **Tool Registry Framework (`tools/registry.py`):**
  - [ ] Build `@register_tool` decorator with automated JSON schema generator for Ankit's agent.
  - [ ] Implement safe `file_read` and `file_write` tools with directory boundary checks.
- [ ] **Deliverable Generators (`doc_generate.py`):**
  - [ ] **Word Approval Note (`python-docx`):** Generate formatted MRPL approval document with corporate header, metadata table, corrosion findings, and signature box.
  - [ ] **Excel Generator (`openpyxl`):** Auto-format procurement and telemetry tables with formulas.
  - [ ] **PowerPoint Generator (`python-pptx`):** Create summary slide decks.
- [ ] **OCR & Vision Tools:**
  - [ ] Wrap `qwen2.5vl:3b` in `ocr_extract.py` to extract text from scanned reports.
  - [ ] Implement `image_analyze.py` to detect valves and tags in engineering drawings.

---

## 🎨 PRAGYAN — Frontend Lead & Interactive Chat / Agent UX Engineer

> **Primary Focus:** Next.js 15 App Router architecture, Bun runtime, Tailwind CSS, Cult UI / shadcn integration, real-time SSE stream consumer, conversational feed, thought visualizer, and file download cards.

### 📁 Files Owned by Pragyan
* `frontend/app/layout.tsx`
* `frontend/app/chat/page.tsx`
* `frontend/components/shared/Sidebar.tsx`
* `frontend/components/chat/ChatWindow.tsx`
* `frontend/components/chat/MessageBubble.tsx`
* `frontend/components/chat/StreamConsumer.ts`
* `frontend/components/chat/FileUploadZone.tsx`
* `frontend/components/chat/ModelBadge.tsx`
* `frontend/components/agent/AgentStepCard.tsx`
* `frontend/components/agent/DeliverableCard.tsx`

### 📋 Pragyan's Checklist
- [ ] **Frontend Foundation & Design System:**
  - [ ] Initialize `frontend/` with Next.js 15, Bun runtime, TypeScript, and Tailwind CSS.
  - [ ] Integrate Cult UI / shadcn components (Button, Input, Card, Badge, Accordion, ScrollArea, Tabs, Dialog).
  - [ ] Apply dark industrial refinery theme (slate `#090d16`, amber `#f59e0b`, emerald `#10b981`).
  - [ ] Build responsive root layout with collapsible navigation sidebar and top system status bar.
- [ ] **Interactive Streaming Chat (`/chat`):**
  - [ ] Conversational feed with auto-scroll and history loading.
  - [ ] Auto-expanding multiline prompt textarea with keyboard shortcuts (Enter to send, Shift+Enter for newline).
  - [ ] Conversation sidebar: create new conversation, switch active chat, delete chat.
- [ ] **Real-Time SSE Stream Consumer (`StreamConsumer.ts`):**
  - [ ] Implement `fetch` stream reader consuming `metadata`, `step`, `token`, and `done` events from Ankit's API.
  - [ ] Token-by-token markdown rendering (`react-markdown` + syntax highlighter + copy code button).
  - [ ] Render dynamic `ModelBadge` showing which model is actively answering (Llama, Qwen-Coder, Qwen-VL).
- [ ] **File Drag & Drop in Chat (`FileUploadZone.tsx`):**
  - [ ] Drag-and-drop file target in chat input.
  - [ ] Call Amit's `POST /api/files/upload`, display attachment chips with thumbnails, and pass `file_ids`.
- [ ] **Agent Reasoning Visualizer (`AgentStepCard.tsx`):**
  - [ ] Accordion showing agent's real-time inner monologue:
    - [ ] 📋 **Plan:** Goal breakdown.
    - [ ] ⚙️ **Action:** Tool being executed with live spinner.
    - [ ] 👁️ **Observation:** Tool output summary.
    - [ ] 💡 **Reflection:** Task validation.
- [ ] **Deliverable Download Card (`DeliverableCard.tsx`):**
  - [ ] Render download card for generated `.docx` / `.xlsx` files with direct download button.

---

# 🚀 PART 2: AI-ASSISTED DEVELOPERS (BEGINNERS)

> **How to Work:** Rahul, Basudev, and Pritam have **completely isolated, self-contained tasks**.  
> For each task, you can copy the **exact AI prompt** provided below into ChatGPT / Claude / Copilot to generate your code without getting confused!

---

## 🚀 RAHUL — Document Parsing & Demo Dataset Curation

> **Role:** Write document text extractors and prepare test refinery files.  
> **Mentor / Code Reviewer:** AMIT

### 📁 Files Owned by Rahul
* `backend/app/rag/parser.py`
* `backend/app/rag/chunker.py`
* `samples/inspection_report.pdf`
* `samples/pid_drawing.png`
* `samples/refinery_sop.txt`
* `samples/financial_data.xlsx`

### 📋 Rahul's Checklist
- [ ] **Document Parser (`parser.py`):**
  - [ ] Write `parse_pdf(file_path)` using `fitz` (`PyMuPDF`) to extract text from digital PDFs.
  - [ ] Write `parse_docx(file_path)` using `python-docx` to extract text from Word files.
  - [ ] Write `parse_txt(file_path)` to read `.txt` and `.md` files in UTF-8.
  - [ ] Create master `parse_document(file_path)` routing by file extension.
- [ ] **Text Chunker (`chunker.py`):**
  - [ ] Write sliding-window chunking function (512 tokens per chunk with 64-token overlap).
  - [ ] Split on paragraph/sentence boundaries so thoughts aren't cut mid-sentence.
- [ ] **Demo Datasets Curation (`samples/`):**
  - [ ] Create `refinery_sop.txt`: Standard operating procedure for MRPL Crude Distillation Unit (CDU) corrosion monitoring.
  - [ ] Create or source `inspection_report.pdf`: 2-page sample inspection report with corrosion thickness readings.
  - [ ] Create `pid_drawing.png`: Sample P&ID schematic showing tower T-101 and safety relief valves.
  - [ ] Create `financial_data.xlsx`: Sample vendor procurement sheet.

### 🤖 AI Prompts for Rahul to Copy-Paste:
```text
PROMPT FOR CHATGPT/CLAUDE:
"Write a Python module named `parser.py` using `fitz` (PyMuPDF) and `docx` (python-docx).
It must contain:
1. `parse_pdf(file_path: str) -> str`
2. `parse_docx(file_path: str) -> str`
3. `parse_txt(file_path: str) -> str`
4. `async def parse_document(file_path: str) -> str` that checks the file extension and calls the right parser.
Include clean error handling and return plain text."
```
```text
PROMPT FOR CHUNKER:
"Write a Python function `chunk_text(text: str, chunk_size: int = 512, overlap: int = 64) -> list[dict]`
that splits text into chunks while trying to preserve sentence endings. Return a list of dicts with `chunk_index` and `content`."
```

---

## 🚀 BASUDEV — Local Embeddings & SQLite RAG Search

> **Role:** Generate local vector embeddings with Ollama and implement SQLite hybrid search.  
> **Mentor / Code Reviewer:** ANKIT

### 📁 Files Owned by Basudev
* `backend/app/rag/embedder.py`
* `backend/app/rag/retriever.py`
* `backend/app/rag/pipeline.py`
* `backend/app/api/knowledge.py`
* `backend/app/tools/knowledge_search.py`

### 📋 Basudev's Checklist
- [ ] **Ollama Vector Embedder (`embedder.py`):**
  - [ ] Write `get_embedding(text: str) -> list[float]` calling `ollama.AsyncClient().embed(model="llama3.2:1b", input=text)`.
  - [ ] Write serialization helper to convert `list[float]` into a binary blob (`bytes`) for SQLite storage.
- [ ] **SQLite FTS5 & Vector Hybrid Retriever (`retriever.py`):**
  - [ ] Keyword search: run query against SQLite FTS5 table `chunks_fts`.
  - [ ] Vector search: compute cosine similarity between query embedding and stored chunk blobs using NumPy.
  - [ ] Combine ranks using **Reciprocal Rank Fusion (RRF)**: $Score = \frac{1}{60 + Rank_{FTS}} + \frac{1}{60 + Rank_{Vector}}$.
  - [ ] Return top 5 most relevant chunks.
- [ ] **RAG Orchestration Pipeline (`pipeline.py`):**
  - [ ] Connect ingestion flow: Rahul's parser ➔ Rahul's chunker ➔ embedder ➔ store in DB.
- [ ] **Knowledge Base API & Search Tool (`knowledge.py` & `knowledge_search.py`):**
  - [ ] `POST /api/knowledge/index`: accepts file ID, triggers RAG ingestion.
  - [ ] `POST /api/knowledge/search`: returns matched text chunks with document citations.
  - [ ] `knowledge_search` tool: wrap retrieval so Ankit's agent can call it during planning.

### 🤖 AI Prompts for Basudev to Copy-Paste:
```text
PROMPT FOR CHATGPT/CLAUDE:
"Write a Python module `embedder.py` using `ollama.AsyncClient`.
1. An async function `get_embedding(text: str, model: str = 'llama3.2:1b') -> list[float]` that calls client.embed.
2. Helper functions `embedding_to_bytes(vec: list[float]) -> bytes` and `bytes_to_embedding(b: bytes) -> list[float]` using struct or numpy."
```
```text
PROMPT FOR HYBRID RETRIEVER:
"Write a Python module `retriever.py` that implements Reciprocal Rank Fusion (RRF).
Given two ranked lists of chunk IDs:
1. `fts_results: list[str]` (from SQLite full text search)
2. `vector_results: list[tuple[str, float]]` (from cosine similarity)
Combine them using formula: score = sum(1.0 / (60 + rank))
Return top K ranked chunk IDs with their combined scores."
```

---

## 🚀 PRITAM — Air-Gap Network Audit, Secondary Workspaces & Presentation

> **Role:** Build network sovereignty checker API, secondary frontend pages, and presentation slides.  
> **Mentor / Code Reviewer:** PRAGYAN

### 📁 Files Owned by Pritam
* `backend/app/api/network.py`
* `backend/app/api/health.py`
* `frontend/app/page.tsx` (Dashboard)
* `frontend/app/knowledge/page.tsx` (KB Manager UI)
* `frontend/app/network/page.tsx` (Air-Gap Monitor UI)
* `frontend/app/tasks/page.tsx` (Task History)
* `frontend/app/settings/page.tsx` (Settings)
* `presentation/` & Demo Video Recording

### 📋 Pritam's Checklist
- [ ] **Air-Gap Sovereignty API (`api/network.py`):**
  - [ ] Use `psutil.net_connections()` to list open TCP/UDP sockets for the app process.
  - [ ] Verify all remote addresses are local (`127.0.0.1`, `0.0.0.0`, or local subnet).
  - [ ] Flag and count any external IP connections (must always be 0).
  - [ ] Return `{ total_connections, external_connections: 0, is_air_gapped: true, connections: [...] }`.
- [ ] **System Health Check (`api/health.py`):**
  - [ ] Check SQLite database status and Ollama availability.
- [ ] **Frontend Secondary Pages (Next.js):**
  - [ ] **Dashboard (`frontend/app/page.tsx`):** System status card, GPU VRAM gauge (~4.1 GB / 100%), and quick launch cards.
  - [ ] **Air-Gap Monitor (`frontend/app/network/page.tsx`):** Table of active local sockets and prominent green **"AIR-GAP STATUS: 100% SECURE / ZERO EXTERNAL CALLS"** badge.
  - [ ] **Knowledge Base UI (`frontend/app/knowledge/page.tsx`):** Upload SOP file button, list of indexed documents, and test search query drawer.
  - [ ] **Task History (`frontend/app/tasks/page.tsx`):** Table showing past agent tasks, steps taken, and tokens consumed.
  - [ ] **Settings (`frontend/app/settings/page.tsx`):** Display loaded models, parameter sizes, and temperature sliders.
- [ ] **Pitch Presentation & Demo Video:**
  - [ ] Create 10-slide PowerPoint presentation following `docs/11_PPT_OUTLINE.md`.
  - [ ] Record a 3-minute screen recording of all 4 demo scenarios as a backup for the judges.

### 🤖 AI Prompts for Pritam to Copy-Paste:
```text
PROMPT FOR NETWORK API:
"Write a FastAPI router in `network.py` using `psutil`.
Implement `GET /api/network/connections` that inspects `psutil.net_connections(kind='inet')`.
Filter out any irrelevant system processes.
Check if any remote address is NOT in ('127.0.0.1', 'localhost', '0.0.0.0', '::1').
Return JSON:
{
  'is_air_gapped': true,
  'external_calls': 0,
  'active_sockets': [{'local': '127.0.0.1:8000', 'remote': '127.0.0.1:3000', 'status': 'ESTABLISHED'}]
}"
```
```text
PROMPT FOR NEXT.JS NETWORK PAGE:
"Write a Next.js 15 React page (`page.tsx`) with Tailwind CSS for a Network Monitor:
1. A large glowing green security badge: 'AIR-GAP STATUS: 100% VERIFIED / ZERO EXTERNAL CALLS'.
2. A refresh button that fetches data from `http://localhost:8000/api/network/connections`.
3. A clean dark table displaying local address, remote address, status, and process.
Use dark slate styling matching a cybersecurity dashboard."
```

---

## 🤝 Cross-Developer Handshake Contracts (Zero Confusion)

1. **Ankit ➔ Pragyan (Streaming Chat SSE):**
   ```text
   event: metadata -> {"conversation_id": "...", "model": "qwen2.5-coder:1.5b", "task_type": "code"}
   event: step     -> {"step_number": 1, "step_type": "act", "content": "Running OCR...", "tool_name": "ocr_extract"}
   event: token    -> {"content": "Found 3 findings."}
   event: done     -> {"task_id": "...", "output_files": ["outputs/MRPL_Approval_Note.docx"]}
   ```

2. **Amit ➔ Rahul & Basudev (File Paths & Models):**
   * Uploaded files stored at: `backend/data/uploads/{id}.{ext}`
   * Generated deliverables at: `backend/data/outputs/{id}.{ext}`
   * Database at: `backend/data/kavach.db`

3. **Rahul ➔ Basudev (RAG Handshake):**
   * Rahul's `parse_document()` outputs clean string text.
   * Rahul's `chunk_text()` outputs `list[dict(chunk_index=int, content=str)]`.
   * Basudev takes these chunks, embeds them with `get_embedding()`, and inserts them into SQLite.

4. **Basudev & Amit ➔ Ankit (Tool Registry):**
   * Basudev registers `knowledge_search` tool in Amit's registry.
   * Amit registers `doc_generate`, `file_read`, and `ocr_extract` tools.
   * Ankit's Agent calls them dynamically via `registry.execute_tool(name, params)`.

5. **Pritam ➔ Pragyan (Workspaces Navigation):**
   * Pritam's pages (`/`, `/knowledge`, `/network`, `/tasks`, `/settings`) use Pragyan's `Sidebar.tsx` and theme tokens.

---

## 🎬 Final Demo Day Role Play (For the Jury)

| Developer | Stage Name | Exact Role in Live Presentation |
|---|---|---|
| 🌟 **ANKIT** | **Lead Presenter & AI Architect** | Explains multi-model routing, why 1B–3B models fit in 4.1GB VRAM, and how the ReAct agent loops autonomously without cloud APIs. |
| 🌟 **AMIT** | **Backend & Systems Lead** | Explains on-premise execution, the msgspec serialization speedup, and the automated `.docx` approval note generation. |
| 🌟 **PRAGYAN** | **Master UI Driver** | Drives keyboard/mouse: uploads scanned PDF, triggers prompt, watches agent steps stream live, and downloads the generated Word deliverable. |
| 🚀 **RAHUL** | **Data & Multimodal Specialist** | Explains how scanned refinery drawings and P&ID diagrams are processed locally via Qwen2.5-VL OCR. |
| 🚀 **BASUDEV** | **RAG & Knowledge Specialist** | Explains SQLite FTS5 hybrid search + RRF ranking, proving MRPL manuals are queried locally with zero cloud leakage. |
| 🚀 **PRITAM** | **Security & Air-Gap Auditor** | Switches to the `/network` tab on screen to demonstrate the live socket audit proving **Zero External Calls** to the judges. |
