# 🛡️ Kavach AI — Master 6-Member Team TODO & Work Allocation

> **Project:** Kavach AI (Air-Gapped Agentic AI Workbench for PSUs & Critical Infrastructure)  
> **Problem Statement ID:** 26117 | **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)  
> **Team Roster:**  
> - 🌟 **Heavy Technical Core Pillars:** **ANKIT** & **AMIT**  
> - 🎨 **Frontend Lead & Chat UX:** **BASUDEV**  
> - 📊 **Pitch Deck, PPT & Demo Lead (Light Tech):** **PRAGYAN**  
> - 🚀 **Data & Ingestion Specialist:** **RAHUL**  
> - 💻 **Security Audit & Workspaces:** **PRITAM**  

---

## 👥 Team Matrix & Ownership Map

```text
┌────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                              KAVACH AI — 6-MEMBER TEAM MATRIX                                          │
├──────────────────────────┬──────────────────────────┬──────────────────────────┬───────────────────────────────────────┤
│ 🌟 ANKIT (Core Pillar)   │ 🌟 AMIT (Core Pillar)    │ 🎨 BASUDEV (Frontend Lead│ 📊 PRAGYAN (PPT & Pitch Lead)         │
│ Team Lead & Core AI      │ Backend & Deliverables   │ Chat & Agent UX          │ High-Impact Presentation & Demo Story │
│                          │                          │                          │                                       │
│ • Ollama Model Lifecycle │ • Tortoise ORM + SQLite  │ • Next.js 15 + Cult UI   │ • 10-Slide Winning PPT Deck           │
│ • Heuristic Model Router │ • msgspec Serialization  │ • SSE Stream Consumer    │ • Jury Pitch Script & Storyline       │
│ • ReAct Agent Planner    │ • File Upload / Storage  │ • Interactive Chat Page  │ • MRPL Problem-Solution Framing       │
│ • Execution & Reflection │ • Tool Registry Base     │ • Agent Step Visualizer  │ • Competitor Feature Matrix           │
│ • Sandboxed Code Runner  │ • Word/Excel Deliverables│ • Deliverable Download   │ • Demo Testing & Scenario QA (Light)  │
│ • Chat & Agent SSE APIs  │ • RAG Engine & Embeddings│ • Layout & UI Themes     │                                       │
├──────────────────────────┴──────────────────────────┴──────────────────────────┼───────────────────────────────────────┤
│ 🚀 RAHUL (Data & Ingestion Specialist)                                         │ 💻 PRITAM (Security Audit & Workspaces│
│ • Document Parsers (PyMuPDF, python-docx, text)                                │ • Air-Gap Network Audit API (psutil)  │
│ • Text Chunker (512-token sliding window)                                      │ • Next.js Network Monitor Page UI     │
│ • Demo Refinery Datasets (P&ID, Inspection PDF, SOPs)                          │ • Dashboard & Settings UI Pages       │
└────────────────────────────────────────────────────────────────────────────────┴───────────────────────────────────────┘
```

---

# 🌟 PART 1: CORE PILLARS (MISSION-CRITICAL HEAVY WORK)

---

## 🧑‍💻 ANKIT — Team Lead & AI Agent Core Architect

> **Primary Focus:** All mission-critical AI logic: GPU model lifecycle, multi-model auto-selection router, autonomous ReAct agent engine with self-correction, code execution sandbox, and core streaming endpoints.

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
- [x] **Repository Setup & Governance:**
  - [x] Initialize monorepo structure (`backend/`, `frontend/`, `samples/`).
  - [x] Configure Python `uv` package manager and lockfile.
  - [x] Verify local Ollama server and pull all 3 models (`llama3.2:1b`, `qwen2.5-coder:1.5b`, `qwen2.5vl:3b`).
- [x] **Ollama Client & GPU Hot-Swap (`ollama_client.py`):**
  - [x] Build async wrapper around `ollama.AsyncClient`.
  - [x] Write startup preloading routine with `keep_alive=-1` to lock all 3 models in GPU memory (~4.1 GB total VRAM).
- [x] **Model Auto-Selection Router (`classifier.py` & `router.py`):**
  - [x] Implement heuristic keyword + attachment classifier:
    - [x] If images or P&ID diagrams attached ➔ `qwen2.5vl:3b`
    - [x] If scanned PDF and OCR keywords present ➔ `qwen2.5vl:3b`
    - [x] If programming keywords or code blocks present ➔ `qwen2.5-coder:1.5b`
    - [x] Default / General chat / Summaries ➔ `llama3.2:1b`
  - [x] Support explicit user override flag (`model_override`).
- [x] **Autonomous ReAct Agent Loop (`app/agent/`):**
  - [x] `planner.py`: Generate structured step plan using local LLM.
  - [x] `executor.py`: Dispatch steps to Amit's Tool Registry.
  - [x] `observer.py`: Inspect tool outputs and detect errors.
  - [x] `loop.py`: Run Plan ➔ Act ➔ Observe ➔ Reflect loop with 10-step limit and error self-correction.
- [x] **Sandboxed Code Runner (`code_execute.py`):**
  - [x] Secure `asyncio.create_subprocess_exec` runner with 30s timeout, memory limit, and stdout/stderr capture.
- [x] **Streaming API Handlers:**
  - [x] `POST /api/chat`: SSE token streaming with metadata event.
  - [x] `POST /api/agent/execute`: SSE step-by-step progress streaming.

---

## 🧑‍💻 AMIT — Backend Systems, Database, Deliverables & RAG Engine

> **Primary Focus:** All mission-critical backend infrastructure: SQLite WAL database, Tortoise ORM models, msgspec serialization, file upload/storage pipeline, tool registry, concrete deliverable generators (Word, Excel), and the RAG hybrid search pipeline.

### 📁 Files Owned by Amit
* `backend/app/core/database.py`
* `backend/app/core/msgspec_adapter.py`
* `backend/app/models/*.py` (`conversation.py`, `message.py`, `agent_task.py`, `agent_step.py`, `tool_call.py`, `document.py`, `knowledge_chunk.py`, `file_upload.py`)
* `backend/app/schemas/*.py` (`chat.py`, `agent.py`, `files.py`, `common.py`)
* `backend/app/api/files.py`
* `backend/app/tools/registry.py`
* `backend/app/tools/file_read.py` & `backend/app/tools/file_write.py`
* `backend/app/tools/doc_generate.py`
* `backend/app/tools/ocr_extract.py` & `backend/app/tools/image_analyze.py`
* `backend/app/rag/embedder.py`, `retriever.py`, `pipeline.py`, `knowledge_search.py`

### 📋 Amit's Checklist
- [ ] **Database & ORM Setup (`database.py` & `models/`):**
  - [ ] Configure Tortoise ORM with `aiosqlite` targeting `backend/data/kavach.db`.
  - [ ] Enable SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
  - [ ] Implement all Tortoise models: `Conversation`, `Message`, `AgentTask`, `AgentStep`, `ToolCall`, `Document`, `KnowledgeChunk`, `FileUpload`.
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
- [ ] **RAG Engine & Local Retrieval (`rag/`):**
  - [ ] Connect Rahul's parser & chunker into SQLite FTS5 table + vector embeddings.
  - [ ] Implement hybrid search (BM25 + Cosine + RRF) and expose `knowledge_search` tool for Ankit's agent.

---

# 🎨 PART 2: FRONTEND LEAD & CHAT EXPERIENCE

---

## 🎨 BASUDEV — Frontend Lead & Interactive Chat / Agent UX Engineer

> **Primary Focus:** Next.js 15 App Router architecture, Bun runtime, Tailwind CSS, Cult UI / shadcn integration, real-time SSE stream consumer, conversational feed, thought visualizer, and deliverable download cards.

### 📁 Files Owned by Basudev
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

### 📋 Basudev's Checklist
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

# 📊 PART 3: PPT, PITCH DECK & DEMO STORYTELLING LEAD

---

## 📊 PRAGYAN — Pitch Deck, PPT & Demo Lead *(Less Technical, High Impact)*

> **Primary Focus:** The presentation deck is what wins the hackathon! Pragyan creates the master pitch deck, refines the MRPL refinery problem narrative, coordinates the live demo storyline, and performs lightweight testing on sample questions.

### 📁 Files & Deliverables Owned by Pragyan
* `presentation/Kavach_AI_MRPL_Pitch_Deck.pptx` (or `.pdf`)
* `docs/11_PPT_OUTLINE.md` (Review and customize)
* `docs/12_VIDEO_SCRIPT.md` (Demo recording narrative)
* `docs/10_DEMO_SCRIPT.md` (Timing & talking points)
* Testing & QA of sample questions on the UI

### 📋 Pragyan's Checklist (Focused on PPT & Presentation)
- [ ] **Master 10-Slide Pitch Presentation (`docs/11_PPT_OUTLINE.md`):**
  - [ ] **Slide 1: Title Card:** Kavach AI (कवच) — Sovereign On-Premises Agentic AI Workbench for MRPL.
  - [ ] **Slide 2: The Core Dilemma:** Classified refinery data (P&ID drawings, inspection reports, crude financial schemas) cannot traverse public cloud AI.
  - [ ] **Slide 3: Our Solution:** 100% on-premises GPU workbench with zero outbound network packets.
  - [ ] **Slide 4: Core Innovation (Multi-Model Hot-Swap):** Why 3 specialized SLMs (1B–3B) beat 1 huge cloud LLM on-prem (~4.1 GB VRAM).
  - [ ] **Slide 5: ReAct Agent Architecture:** How Kavach acts autonomously (Plan ➔ Act ➔ Observe ➔ Reflect) and self-corrects.
  - [ ] **Slide 6: Real Deliverables vs Chat Text:** Emphasize real Word approval notes, Excel sheets, and code execution.
  - [ ] **Slide 7: Multimodal Intelligence:** Processing scanned corrosion inspection reports & engineering diagrams.
  - [ ] **Slide 8: Air-Gap Verification:** Live socket monitoring proving zero external calls.
  - [ ] **Slide 9: Competitor Matrix:** Kavach vs Copilot on-prem, Open-WebUI, Ollama bare-metal, Dify (based on `docs/13_COMPETITOR_ANALYSIS.md`).
  - [ ] **Slide 10: Scalability, Business ROI & Roadmap:** MRPL multi-unit deployment & future roadmap.
- [ ] **Demo Narrative & Jury Rehearsal:**
  - [ ] Write exact speaker script for Ankit, Amit, Basudev, and yourself.
  - [ ] Prepare answers for tough judge questions: *"Why not just use ChatGPT Enterprise?"*, *"How do you handle hallucination?"*, *"What happens without GPU?"*
- [ ] **Lightweight Quality Testing (QA):**
  - [ ] Test the 4 demo prompts on Basudev's `/chat` interface.
  - [ ] Verify generated `.docx` file formatting looks clean and professional.

---

# 🚀 PART 4: SUPPORTING MODULES & SPECIALISTS

---

## 🚀 RAHUL — Document Parsing & Demo Datasets

> **Primary Focus:** Text extractors for PDF/Word, text chunker, and curating realistic refinery sample data.  
> **Mentor / Reviewer:** AMIT

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

---

## 💻 PRITAM — Air-Gap Network Audit & Secondary Workspaces

> **Primary Focus:** Network sovereignty audit API, secondary frontend pages (Network Monitor, Dashboard, Settings), and backup video recording.  
> **Mentor / Reviewer:** BASUDEV & ANKIT

### 📁 Files Owned by Pritam
* `backend/app/api/network.py`
* `backend/app/api/health.py`
* `frontend/app/page.tsx` (Dashboard)
* `frontend/app/knowledge/page.tsx` (KB Manager UI)
* `frontend/app/network/page.tsx` (Air-Gap Monitor UI)
* `frontend/app/tasks/page.tsx` (Task History)
* `frontend/app/settings/page.tsx` (Settings)
* Backup Screen Recording Video (using Pragyan's video script)

### 📋 Pritam's Checklist
- [ ] **Air-Gap Sovereignty API (`api/network.py`):**
  - [ ] Use `psutil.net_connections()` to list open TCP/UDP sockets for the app process.
  - [ ] Verify all remote addresses are local (`127.0.0.1`, `0.0.0.0`, or local subnet).
  - [ ] Return `{ total_connections, external_connections: 0, is_air_gapped: true, connections: [...] }`.
- [ ] **System Health Check (`api/health.py`):**
  - [ ] Check SQLite database status and Ollama availability.
- [ ] **Frontend Secondary Pages (Next.js):**
  - [ ] **Dashboard (`frontend/app/page.tsx`):** System status card, GPU VRAM gauge (~4.1 GB / 100%), and quick launch cards.
  - [ ] **Air-Gap Monitor (`frontend/app/network/page.tsx`):** Table of active local sockets and prominent green **"AIR-GAP STATUS: 100% SECURE / ZERO EXTERNAL CALLS"** badge.
  - [ ] **Knowledge Base UI (`frontend/app/knowledge/page.tsx`):** Upload SOP file button and document index list.
  - [ ] **Task History (`frontend/app/tasks/page.tsx`):** Table showing past agent tasks and token usage.
- [ ] **Demo Backup Video:**
  - [ ] Record a 3-minute screen recording of all 4 demo scenarios following Pragyan's script as insurance for the jury.

---

## 🤝 Handshake Flow Between Team Members

```
[RAHUL: Samples & Parsers] ──► [AMIT: Database & Deliverable Tools] ──► [ANKIT: ReAct Agent Loop]
                                                                                │
                                                                                ▼
[PRITAM: Network Monitor] ◄── [BASUDEV: Chat & Step Visualizer UI] ◄──── [ANKIT: SSE Streaming]
             │                                     │
             ▼                                     ▼
[PRAGYAN: Verifies Demo Scenarios on UI & Leads Winning PPT Pitch Deck for Jury]
```

---

## 🎬 Demo Presentation Lineup

| Member | Presentation Role | What to Do in Front of the Judges |
|---|---|---|
| 📊 **PRAGYAN** | **Master Storyteller & Pitch Lead** | Opens the pitch with the MRPL problem statement, walks through the 10-slide deck, and introduces the live demo. |
| 🌟 **ANKIT** | **AI Architect** | Explains the multi-model router, GPU preloading (`keep_alive=-1`), and ReAct agent planning. |
| 🌟 **AMIT** | **Backend Lead** | Explains on-premise execution, the msgspec serialization speedup, and the automated `.docx` approval note generation. |
| 🎨 **BASUDEV** | **Master UI Driver** | Drives keyboard/mouse live: uploads scanned PDF, triggers prompt, watches agent steps stream, and downloads Word deliverable. |
| 🚀 **RAHUL** | **Data Specialist** | Explains how scanned refinery drawings and P&ID diagrams are parsed locally via Qwen2.5-VL. |
| 💻 **PRITAM** | **Security Auditor** | Switches to the `/network` tab on screen to demonstrate the live socket audit proving **Zero External Calls** to the judges. |
