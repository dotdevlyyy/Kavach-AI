# KAVACH AI (कवच) — Sovereign On-Premise Agentic AI Workbench

> **Problem Statement ID:** 26117
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)
> **Theme:** Smart Automation | **Category:** Software
> **SIH 2026**

---

## 📋 Documentation Index

| # | Document | Description |
|---|---|---|
| 01 | [Project Overview](01_PROJECT_OVERVIEW.md) | Vision, differentiators, target users, success metrics, scope |
| 02 | [Problem Analysis](02_PROBLEM_ANALYSIS.md) | Core problem, market gap, MRPL context, pain points, severity |
| 03 | [Solution Architecture](03_SOLUTION_ARCHITECTURE.md) | System diagram, component breakdown, request flows, deployment |
| 04 | [Tech Stack](04_TECH_STACK.md) | Every technology choice with justification (Next.js, Bun, FastAPI, UV, msgspec, Tortoise ORM, SQLite, Ollama, Cult UI) |
| 05 | [Database Schema](05_DATABASE_SCHEMA.md) | Tortoise ORM models, ERD, FTS5 config, SQLite setup |
| 06 | [API Specification](06_API_SPEC.md) | All endpoints, msgspec request/response schemas, SSE streaming |
| 07 | [Model Router & Agent Engine](07_MODEL_ROUTER_AND_AGENT.md) | Task classifier, routing table, ReAct loop, tool registry, model preloading |
| 08 | [RAG Pipeline](08_RAG_PIPELINE.md) | Ingestion, chunking, embedding, hybrid search, knowledge base |
| 09 | [10-Day Implementation Plan](09_10_DAY_PLAN.md) | Day-by-day tasks, team assignments, critical path |
| 10 | [Demo Script](10_DEMO_SCRIPT.md) | 5 demo scenarios, talking points, judge Q&A, fallback plan |
| 11 | [PPT Outline](11_PPT_OUTLINE.md) | 10-slide structure with visual suggestions |
| 12 | [Video Script](12_VIDEO_SCRIPT.md) | 3-5 minute video with scene-by-scene voiceover |
| 13 | [Competitor Analysis](13_COMPETITOR_ANALYSIS.md) | 6 direct competitors + 6 cloud platforms, feature matrix |
| 14 | [Risk Mitigation](14_RISK_MITIGATION.md) | 10 risks with mitigations, edge cases |
| 15 | [5-Developer Task List (TODO)](../TODO.md) | Full end-to-end task matrix & checkboxes for 5 developers |

---

## 🛠 Tech Stack Summary

| Layer | Technology | Why |
|---|---|---|
| **Frontend** | Next.js 15 + Bun + Cult UI + Tailwind | Agent chat patterns, 4x faster installs |
| **Backend** | FastAPI + UV + msgspec | 10x faster serialization, async-native |
| **Database** | SQLite + Tortoise ORM + FTS5 | Zero-setup, async ORM, built-in full-text search |
| **AI** | Ollama + Llama 3.2:1b + Qwen2.5-Coder:1.5b + Qwen2.5-VL:3b | 3 models, ~4.1 GB total, all preloaded |
| **Packages** | UV (Python) + Bun (JS) | 100x faster than pip, 4x faster than npm |

---

## 🧠 Models

| Model | Purpose | Size | VRAM |
|---|---|---|---|
| `llama3.2:1b` | General chat, summarization, document drafting | 1B | ~0.8 GB |
| `qwen2.5-coder:1.5b` | Code generation, review, debugging | 1.5B | ~1.1 GB |
| `qwen2.5vl:3b` | Vision, OCR, image analysis, scanned documents | 3B | ~2.2 GB |

All models preloaded at startup with `keep_alive=-1` (never unloaded) for instant switching.

---

## 🏗 Monorepo Structure

```
kavach-ai/
├── frontend/          # Next.js 15 + Bun + Cult UI
├── backend/           # FastAPI + UV + msgspec + Tortoise ORM
├── scripts/           # Setup scripts (install + pull models)
├── samples/           # Demo data (scanned PDFs, images, Excel)
├── README.md
└── LICENSE            # MIT
```

---

## 🚀 Quick Start

```bash
# 1. Install Ollama
# Windows: Download from https://ollama.com/download
# Linux: curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull models
ollama pull llama3.2:1b
ollama pull qwen2.5-coder:1.5b
ollama pull qwen2.5vl:3b

# 3. Backend
cd backend
uv sync
uv run uvicorn app.main:app --reload --port 8000

# 4. Frontend
cd frontend
bun install
bun run dev

# 5. Open http://localhost:3000
```

---

## 🎯 Demo Checklist

- [ ] All 3 models loaded (`ollama ps` shows 3 models)
- [ ] Backend running on :8000 (`/api/health` returns green)
- [ ] Frontend running on :3000
- [ ] Model auto-selection working (code → Qwen-Coder, general → Llama)
- [ ] Vision/OCR working (upload image → Qwen-VL processes it)
- [ ] Agent task end-to-end (upload PDF → extract → draft DOCX)
- [ ] Code sandbox working (generate code → execute → show output)
- [ ] Network monitor showing 0 external connections
- [ ] Backup video loaded in PPT
