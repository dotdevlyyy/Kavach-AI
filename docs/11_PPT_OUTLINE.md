# 11 — PPT Outline

> **Duration:** Max 10 slides for judges
> **Style:** Minimal text, maximum visuals

---

## Slide 1: Title Slide

**KAVACH AI** (कवच — Armour)
*Sovereign On-Premise Agentic AI Workbench*

- Team Name
- PS ID: 26117 | Organization: MRPL
- SIH 2026

---

## Slide 2: The Problem

**Visual:** Split screen — Left: Engineer drowning in papers. Right: Data leaking to cloud.

**Key Text:**
- PSUs generate sensitive knowledge work daily (approval notes, code, reports, drawings)
- Cloud AI (ChatGPT, Copilot) = data leakage risk
- Manual work = 20-30% productivity loss
- Shadow AI usage growing — organizations have no control

**One-liner:** *"They either do it manually, or they quietly paste confidential data into public AI tools."*

---

## Slide 3: Our Solution

**Visual:** Kavach AI dashboard screenshot / architecture diagram

**Key Text:**
- Self-hosted, air-gapped AI workbench
- 3 specialized open-weight models, auto-selected per task
- True agentic execution with tool use
- Multimodal: scanned PDFs, drawings, images
- Real outputs: Word, Excel, PowerPoint, working code
- Zero external network calls — provable

---

## Slide 4: How Model Auto-Selection Works

**Visual:** Flow diagram showing user message → classifier → model selection

```
"Write a Python script..."   → qwen2.5-coder:1.5b (Code)
"Summarize this report..."   → llama3.2:1b (General)
[Image uploaded]             → qwen2.5vl:3b (Vision)
```

**Key Point:** No manual model switching. Router classifies task type → picks optimal model → instant switch (all models preloaded in VRAM).

---

## Slide 5: Agentic Workflow (End-to-End Example)

**Visual:** Step-by-step flow of the inspection report → approval note demo

```
Step 1: USER uploads scanned inspection report
Step 2: AGENT plans → "I'll OCR the PDF, extract findings, draft a note"
Step 3: AGENT calls OCR tool → Qwen2.5-VL extracts text
Step 4: AGENT calls KB search → finds relevant SOP sections
Step 5: AGENT calls doc_generate → creates Word approval note
Step 6: USER downloads the completed document

Manual time: 2-3 hours → Kavach time: 30 seconds
```

---

## Slide 6: Tech Stack

**Visual:** Architecture blocks with logos

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 + Bun + Cult UI |
| Backend | FastAPI + UV + msgspec |
| Database | SQLite + Tortoise ORM + FTS5 |
| AI | Ollama + Llama 3.2 + Qwen2.5-Coder + Qwen2.5-VL |
| Infra | Single server. No cloud. No Docker required. |

**Key Point:** Total VRAM: ~4.1 GB for all 3 models. Runs on any mid-range GPU.

---

## Slide 7: Sovereignty Proof

**Visual:** Screenshot of Network Monitor page showing all connections are local

**Key Points:**
- All connections: `127.0.0.1 ↔ 127.0.0.1`
- External connections counter: **0** (throughout entire demo)
- No DNS lookups, no port 443 traffic, no telemetry
- Optional: Wireshark capture as evidence
- Ollama configured as localhost-only
- All models pre-downloaded, all packages vendored

**One-liner:** *"Not a claim. A proof."*

---

## Slide 8: Impact & Use Cases

**Visual:** Before/after comparison with time savings

| Use Case | Manual Time | Kavach Time | Savings |
|---|---|---|---|
| Inspection report → approval note | 2-3 hours | 30 seconds | 99% |
| Internal tool scripting | 1 day | 10 minutes | 95% |
| Drawing analysis + findings | 1 hour | 1 minute | 98% |
| SOP-grounded Q&A | 30 min search | 5 seconds | 99% |

**Scale:** MRPL alone has ~2000 engineers. India has 300+ PSUs. The impact multiplies.

---

## Slide 9: Competitive Advantage

**Visual:** Feature comparison matrix

|  | ChatGPT | Open WebUI | AnythingLLM | **Kavach AI** |
|---|---|---|---|---|
| Air-gapped | ✗ | ✓ | ✓ | ✓ |
| Multi-model auto-select | ✗ | ✗ | ✗ | **✓** |
| Agentic (tools, planning) | ~ | ✗ | ~ | **✓** |
| Multimodal (OCR, vision) | ✓ | ~ | ~ | **✓** |
| Document output (DOCX/XLSX) | ✗ | ✗ | ✗ | **✓** |
| Local knowledge base | ✗ | ~ | ✓ | **✓** |

---

## Slide 10: Future Roadmap + Thank You

**Near-term (3-6 months):**
- Larger models (70B+) for multi-GPU servers
- LoRA fine-tuning on org-specific data
- Multi-user RBAC + audit trail

**Long-term (1-2 years):**
- Plugin marketplace (SAP, ERP, SCADA connectors)
- Federated deployment across PSU branches
- Voice interface for field engineers

**Thank you.**
*Live demo follows.*

---

## Design Notes for PPT

- **Color scheme:** Deep navy (#0A1628) + Electric blue (#3B82F6) + White
- **Font:** Inter or Outfit (Google Fonts)
- **Background:** Dark gradient with subtle grid pattern
- **Icons:** Lucide icons for consistency with UI
- **Animations:** Minimal — fade-in for list items only
- **Logo:** Kavach shield icon with Devanagari text
