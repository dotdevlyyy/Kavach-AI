# 09 — 10-Day Implementation Plan

> **Team size:** 6 members
> **Duration:** 10 days (SIH hackathon format)

## Day-by-Day Plan

### Day 1 — Environment Setup + Foundation

**Goal:** Every team member has a working dev environment. Core project structure exists.

| Task | Owner | Status |
|---|---|---|
| Initialize monorepo structure (frontend/ + backend/) | Lead | ☐ |
| Backend: `uv init`, install core deps (fastapi, uvicorn, msgspec, tortoise-orm, ollama) | Backend 1 | ☐ |
| Frontend: `bun create next-app`, install deps, setup Tailwind | Frontend 1 | ☐ |
| Install Ollama, pull all 3 models on every dev machine | All | ☐ |
| Test Ollama SDK: chat, generate, embed with each model | Backend 2 | ☐ |
| Copy Cult UI base components (Button, Card, Input, Dialog) | Frontend 2 | ☐ |
| Setup .gitignore, README, basic project docs | Lead | ☐ |
| Configure ESLint, Prettier, Ruff | Lead | ☐ |

**Deliverable:** Running `uv run uvicorn app.main:app` and `bun run dev` both succeed.

---

### Day 2 — Database + Backend Core

**Goal:** Tortoise ORM models, database initialization, model preloading at startup.

| Task | Owner | Status |
|---|---|---|
| Define all Tortoise ORM models (conversation, message, tool_call, etc.) | Backend 1 | ☐ |
| Database initialization + schema generation in lifespan | Backend 1 | ☐ |
| Implement model preloading at startup (pull + warm up + keep_alive=-1) | Backend 2 | ☐ |
| Implement /api/health endpoint | Backend 2 | ☐ |
| Implement /api/models and /api/models/ps endpoints | Backend 2 | ☐ |
| msgspec adapter for FastAPI (MsgspecJSONResponse) | Backend 1 | ☐ |
| Frontend: App layout (sidebar nav, main content area) | Frontend 1 | ☐ |
| Frontend: Settings page (model status, system info) | Frontend 2 | ☐ |

**Deliverable:** Backend starts, creates DB, preloads all 3 models, health check returns green.

---

### Day 3 — Model Router + Basic Chat

**Goal:** Task classification and model auto-selection working. Basic chat functional.

| Task | Owner | Status |
|---|---|---|
| Implement task classifier (keyword + heuristic based) | Backend 1 | ☐ |
| Implement routing table (TaskType → model mapping) | Backend 1 | ☐ |
| Implement /api/chat endpoint with SSE streaming | Backend 2 | ☐ |
| Conversation CRUD (create, list, get, delete) | Backend 2 | ☐ |
| Frontend: Chat page with Cult UI chat components | Frontend 1 | ☐ |
| Frontend: SSE stream consumer + token-by-token rendering | Frontend 1 | ☐ |
| Frontend: Model badge showing auto-selected model | Frontend 2 | ☐ |
| Frontend: Conversation sidebar (list, create new, switch) | Frontend 2 | ☐ |
| Test: Send messages, verify correct model is selected | All | ☐ |

**Deliverable:** User can chat. Asking a code question routes to Qwen2.5-Coder. General questions route to Llama.

---

### Day 4 — File Upload + Vision/OCR

**Goal:** File uploads work. Vision model processes images and scanned documents.

| Task | Owner | Status |
|---|---|---|
| Implement file upload endpoint (multipart/form-data) | Backend 1 | ☐ |
| Implement file storage (./data/uploads/) | Backend 1 | ☐ |
| Implement OCR tool via Qwen2.5-VL (image → text) | Backend 2 | ☐ |
| Implement image analysis tool via Qwen2.5-VL | Backend 2 | ☐ |
| Integrate vision model into chat (when images attached) | Backend 2 | ☐ |
| Frontend: File upload zone (drag & drop) in chat | Frontend 1 | ☐ |
| Frontend: Image preview in chat messages | Frontend 1 | ☐ |
| Frontend: File attachment indicators | Frontend 2 | ☐ |
| Prepare sample scanned PDFs and images for testing | Design | ☐ |

**Deliverable:** User can upload an image/PDF, AI describes it or extracts text.

---

### Day 5 — Agent Engine + Tool System

**Goal:** ReAct agent loop working with basic tools (file_read, file_write, code_execute).

| Task | Owner | Status |
|---|---|---|
| Implement Tool Registry (register, execute, get descriptions) | Backend 1 | ☐ |
| Implement file_read tool | Backend 1 | ☐ |
| Implement file_write tool | Backend 1 | ☐ |
| Implement code_execute tool (sandboxed subprocess) | Backend 2 | ☐ |
| Implement ReAct agent loop (plan → act → observe → reflect) | Backend 2 | ☐ |
| Implement /api/agent/execute endpoint with SSE streaming | Backend 2 | ☐ |
| Frontend: Agent step visualization (collapsible steps) | Frontend 1 | ☐ |
| Frontend: Tool call display (input → output) | Frontend 1 | ☐ |
| Frontend: Code output display with syntax highlighting | Frontend 2 | ☐ |
| Test: Multi-step coding task (write + execute + iterate) | All | ☐ |

**Deliverable:** Agent can plan a task, call tools, iterate, and complete multi-step work.

---

### Day 6 — Document Generation + Knowledge Base

**Goal:** Agent can generate DOCX/XLSX/PPTX. Knowledge base ingestion works.

| Task | Owner | Status |
|---|---|---|
| Implement doc_generate tool (DOCX via python-docx) | Backend 1 | ☐ |
| Implement doc_generate tool (XLSX via openpyxl) | Backend 1 | ☐ |
| Implement doc_generate tool (PPTX via python-pptx) | Backend 1 | ☐ |
| Implement RAG pipeline: parser + chunker + embedder | Backend 2 | ☐ |
| Implement knowledge base ingestion endpoint | Backend 2 | ☐ |
| Implement FTS5 virtual table + triggers | Backend 2 | ☐ |
| Frontend: Document preview + download button | Frontend 1 | ☐ |
| Frontend: Knowledge base page (upload, list, delete docs) | Frontend 2 | ☐ |
| Test: Generate a Word approval note end-to-end | All | ☐ |

**Deliverable:** Agent generates real documents. KB accepts and indexes documents.

---

### Day 7 — RAG Search + Network Monitor

**Goal:** Knowledge base search integrated into chat. Sovereignty proof via network monitor.

| Task | Owner | Status |
|---|---|---|
| Implement hybrid search (FTS5 + semantic + RRF) | Backend 1 | ☐ |
| Implement knowledge_search tool for agent | Backend 1 | ☐ |
| Integrate RAG context into chat prompts | Backend 1 | ☐ |
| Implement /api/network/connections endpoint (netstat parsing) | Backend 2 | ☐ |
| Implement network logging (periodic netstat capture) | Backend 2 | ☐ |
| Frontend: Citation display in chat (source document links) | Frontend 1 | ☐ |
| Frontend: Network monitor page (live connections table) | Frontend 2 | ☐ |
| Frontend: "Zero External Calls" badge / indicator | Frontend 2 | ☐ |
| Test: Ask question grounded in KB document | All | ☐ |

**Deliverable:** Chat uses KB context with citations. Network monitor shows all connections are local.

---

### Day 8 — Integration + Demo Scenarios

**Goal:** All pieces connected. Practice demo scenarios end-to-end.

| Task | Owner | Status |
|---|---|---|
| End-to-end test: Scanned inspection report → approval note (DOCX) | Backend 1 | ☐ |
| End-to-end test: Code generation → sandbox execution → output | Backend 2 | ☐ |
| End-to-end test: Image/drawing analysis with findings | Backend 2 | ☐ |
| End-to-end test: KB-grounded Q&A with citations | Backend 1 | ☐ |
| Frontend: Dashboard page (system status, recent tasks, model health) | Frontend 1 | ☐ |
| Frontend: Task history page (view past agent workflows) | Frontend 2 | ☐ |
| Prepare demo data (sample reports, drawings, SOPs) | Design | ☐ |
| Fix all bugs found during integration testing | All | ☐ |

**Deliverable:** All 4 demo scenarios run smoothly without errors.

---

### Day 9 — Polish + Presentation

**Goal:** UI polish, error handling, presentation preparation.

| Task | Owner | Status |
|---|---|---|
| UI polish: animations, loading states, error messages | Frontend 1 | ☐ |
| UI polish: responsive layout, dark theme refinement | Frontend 2 | ☐ |
| Backend: Error handling, edge cases, timeout handling | Backend 1 | ☐ |
| Backend: Logging cleanup, structured logs | Backend 2 | ☐ |
| Create PowerPoint presentation | Design | ☐ |
| Write demo script with exact steps and talking points | Lead | ☐ |
| Record backup demo video (in case of live demo failure) | Lead | ☐ |
| Prepare FAQ / anticipated judge questions | All | ☐ |

**Deliverable:** Presentation ready. Demo script rehearsed once.

---

### Day 10 — Rehearsal + Submission

**Goal:** Multiple rehearsals. Final submission.

| Task | Owner | Status |
|---|---|---|
| Full demo rehearsal #1 (time it, note issues) | All | ☐ |
| Fix any issues found in rehearsal | All | ☐ |
| Full demo rehearsal #2 | All | ☐ |
| Ensure Ollama + all models working on demo machine | Lead | ☐ |
| Pre-warm demo queries (cache popular responses) | Backend 1 | ☐ |
| Final git commit + tag v1.0.0 | Lead | ☐ |
| Submit project on SIH portal | Lead | ☐ |
| Keep backup laptop ready with identical setup | All | ☐ |

**Deliverable:** Project submitted. Team confident in demo.

---

## Team Role Assignments

| Role | Count | Responsibilities |
|---|---|---|
| **Lead** | 1 | Architecture decisions, integration, demo script, project management |
| **Backend 1** | 1 | ORM models, API endpoints, RAG pipeline, document generation |
| **Backend 2** | 1 | Ollama integration, model router, agent engine, tools, code sandbox |
| **Frontend 1** | 1 | Chat UI (Cult UI), streaming, agent steps, file upload, document preview |
| **Frontend 2** | 1 | Layout, navigation, network monitor, KB page, settings, dashboard |
| **Design / QA** | 1 | Sample data prep, testing, presentation, video recording |

## Critical Path

```
Day 1: Setup ──► Day 2: DB + Models ──► Day 3: Chat + Router (CRITICAL) 
                                                    │
                                        ┌───────────┴───────────┐
                                        ▼                       ▼
                                Day 4: Vision/OCR        Day 5: Agent Engine
                                        │                       │
                                        └───────────┬───────────┘
                                                    ▼
                                        Day 6: Docs + KB ──► Day 7: RAG + Network
                                                                      │
                                                              Day 8: Integration
                                                                      │
                                                              Day 9: Polish
                                                                      │
                                                              Day 10: Demo
```

**Day 3 is the critical milestone.** If basic chat + model routing doesn't work by end of Day 3, we're behind schedule.

## Risk Mitigation

| Risk | Mitigation |
|---|---|
| Models don't fit in VRAM together | Use CPU inference for smaller models; reduce to 2 models |
| Ollama crashes under load | Pre-warm all queries; add restart logic in health check |
| Agent loop gets stuck | Max 10 steps with timeout; graceful failure with partial results |
| Demo machine different from dev | Dockerize backend; use portable Ollama setup |
| Live demo fails | Pre-recorded backup video loaded in PPT |
| Internet required at venue (for npm/pip) | Vendor all dependencies; bring them on USB drive |
