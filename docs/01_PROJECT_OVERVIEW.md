# 01 — Project Overview

> **Problem Statement ID:** 26117
> **Organization:** Mangalore Refinery and Petrochemicals Limited (MRPL)
> **Theme:** Smart Automation
> **Category:** Software

## Vision

Refineries, PSUs, defence-linked manufacturing units, and government offices generate enormous volumes of routine but **sensitive knowledge work** — approval notes, board presentations, engineering calculations, code for internal tools, review of scanned drawings and inspection reports. None of this can traverse cloud AI services because the data is classified: P&ID diagrams, financials, vendor negotiations, unreleased designs, internal correspondence, and confidential business strategies.

We build **Kavach AI** (कवच — "armour") — a fully self-hosted, air-gapped Agentic AI Workbench that runs entirely on the organization's own GPU server. **Nothing leaves the premises. Ever.** The system auto-selects the optimal open-weight model for each task, acts as a genuine agent (multi-step planning, tool use, iteration), handles multimodal inputs (scanned PDFs, handwritten notes, engineering drawings, photographs), and produces real deliverables — not just chat replies.

## Core Differentiators

| # | Differentiator | Detail |
|---|---|---|
| 1 | **True Air-Gap** | Zero outbound network calls. Provable via network monitor/logs during demo. |
| 2 | **Multi-Model Auto-Selection** | Router automatically picks the right model per task: general chat → Llama 3.2, code → Qwen2.5-Coder, vision/OCR → Qwen2.5-VL. |
| 3 | **Agentic Execution** | Multi-step planning, tool calling (file I/O, code sandbox, spreadsheets, document search), self-correction loops. |
| 4 | **Multimodal Input** | Scanned PDFs, handwritten notes, P&ID drawings, photographs — all processed on-device. |
| 5 | **Real Deliverables** | Outputs Word docs, Excel sheets, PPT files, working code — not just chat text. |
| 6 | **Local Knowledge Base** | Organization's SOPs, manuals, past correspondence grounded via on-prem RAG. |
| 7 | **Model Hot-Swap** | All three models preloaded in GPU memory at startup — instant switching, zero cold-start. |
| 8 | **Extensible Architecture** | New open-weight models addable without redesigning the system. |

## Target Users

### Persona A — Rajesh, Refinery Engineer (MRPL)
- Reviews scanned inspection reports for corrosion findings
- Needs to draft an approval note summarizing findings + recommended action
- **Today:** Manually reads 40-page scanned PDFs, types up summaries in Word, cross-references SOPs
- **With Kavach:** Uploads the scanned report → AI extracts findings → drafts Word approval note in 30 seconds

### Persona B — Sneha, IT Developer (PSU Internal Tools)
- Builds internal Python scripts for data processing pipelines
- Cannot paste proprietary CSV schemas into ChatGPT/Copilot
- **Today:** Writes code manually, searches Stack Overflow for patterns
- **With Kavach:** Describes the task → gets working code → executes in sandbox → iterates until correct

### Persona C — Anand, Procurement Officer (Government Office)
- Prepares board presentations with financial summaries from Excel data
- Data is confidential — vendor pricing, negotiation strategies
- **Today:** Manually creates slides, cross-references spreadsheets
- **With Kavach:** Uploads Excel → AI generates summary slides → exports as PPTX

## Success Metrics (5 Measurable KPIs)

| # | Metric | Target | How Measured |
|---|---|---|---|
| 1 | Model auto-selection accuracy | ≥ 90% correct routing | 20-task eval set across 3 types |
| 2 | End-to-end agentic task completion | ≥ 80% success | 10 multi-step scenarios |
| 3 | OCR + Vision accuracy on scanned docs | ≥ 85% text extraction | 10 sample scanned PDFs |
| 4 | Chat response latency (p95) | < 5s first token | Logged per request |
| 5 | Zero external network calls | 100% local | Wireshark/network monitor during demo |

## Expected Demonstration

1. **Model Auto-Selection** — Show routing across ≥ 2 task types (code + document summary)
2. **Agentic End-to-End Task** — Read a scanned inspection report → extract findings → draft Word approval note
3. **Coding Task** — Generate code, run in sandbox, verify output
4. **Multimodal Task** — Understand an image/scanned document, extract meaningful information
5. **Sovereignty Proof** — Live network monitor showing zero external calls throughout the demo

## Out of Scope (hackathon constraints)

- Voice input/output
- Multi-user authentication and RBAC
- Production-grade horizontal scaling
- Real MRPL proprietary data (use public samples for demo)
- Fine-tuning models on domain data
- Mobile native app

## Future Roadmap (post-SIH)

1. **Larger models** — Scale to 70B+ class when org has multi-GPU servers
2. **Domain fine-tuning** — LoRA adapters trained on org-specific documents
3. **RBAC & audit trail** — Multi-user access with role-based permissions
4. **Workflow automation** — Recurring scheduled tasks (daily report generation)
5. **Plugin marketplace** — Custom tool connectors (SAP, ERP, SCADA integration)
6. **Federated deployment** — Central model registry, satellite workstations
