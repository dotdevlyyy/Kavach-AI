# 02 — Problem Analysis

## The Core Problem

India's industrial backbone — refineries, PSUs, defence manufacturers, government offices — generates terabytes of sensitive knowledge work daily. This work includes:

- **Approval notes** for maintenance shutdowns, equipment replacements, budget allocations
- **Board presentations** summarizing financial performance, project status, risk assessments
- **Engineering calculations** for pressure vessels, piping stress, heat exchanger design
- **Code for internal tools** — automation scripts, data pipelines, dashboard backends
- **Review of scanned drawings** — P&IDs, isometric drawings, GA drawings
- **Inspection reports** — corrosion surveys, NDT reports, safety audits
- **Internal correspondence** — vendor negotiations, strategy memos, confidential circulars

### Why Cloud AI Cannot Be Used

| Barrier | Detail |
|---|---|
| **Data Classification** | P&ID diagrams, financial data, vendor pricing, unreleased designs are classified as confidential or restricted |
| **Regulatory Compliance** | OISD (Oil Industry Safety Directorate), SEBI, DPP (Defence Procurement Procedure) mandate on-premise data handling |
| **Company Policy** | Most PSUs have explicit policies prohibiting upload of internal documents to external servers |
| **IP Risk** | Engineering drawings, proprietary process parameters, catalyst formulations are core IP |
| **Supply Chain Sensitivity** | Vendor negotiations, pricing, contract terms cannot be exposed |

### The Current Reality

```
┌─────────────────────────────────────────────────────────────┐
│                    TODAY'S WORKFLOW                          │
│                                                             │
│  Option A: Manual Work                                      │
│  ├─ Engineer reads 40-page scanned inspection report        │
│  ├─ Manually types findings into Word                       │
│  ├─ Cross-references SOPs from shared drive                 │
│  ├─ Drafts approval note (2-3 hours)                        │
│  └─ Sends for review → corrections → repeat                │
│                                                             │
│  Option B: Shadow AI (the real risk)                        │
│  ├─ Frustrated engineer pastes P&ID details into ChatGPT    │
│  ├─ Gets useful answer in 30 seconds                        │
│  ├─ Confidential data now on OpenAI's servers               │
│  └─ Organization has no visibility or control               │
│                                                             │
│  Result: Either productivity loss OR data leakage           │
└─────────────────────────────────────────────────────────────┘
```

## Market Gap Analysis

### Existing Solutions and Why They Fail

| Solution | Limitation for Industrial Use |
|---|---|
| **ChatGPT / Claude / Gemini** | Cloud-based. Data leaves premises. Non-starter for classified work. |
| **GitHub Copilot** | Cloud-based. Source code sent to Microsoft servers. Banned in most PSUs. |
| **Azure OpenAI (private endpoint)** | Still cloud. Data in Microsoft's datacenter, not on-premise. Requires internet. |
| **Ollama + Open WebUI** | Single-model chat only. No agentic capabilities. No multi-model routing. No document generation. |
| **LM Studio** | Desktop app. Single-model. No agent loop. No tool use. No multimodal. |
| **Text Generation WebUI** | Single-model. No agentic workflow. No document output. |
| **Jan.ai** | Local chat. No multi-step planning. No code sandbox. No document generation. |
| **AnythingLLM** | Closest competitor. Has RAG but no true agentic execution. Single model at a time. No auto-selection. |

### The Gap We Fill

```
                 Multi-Model    Agentic     Multimodal    Document     Air-Gap
                 Auto-Select    (tools,     (OCR, vision  Output       Provable
                                planning)   drawings)     (DOCX/XLSX)
─────────────────────────────────────────────────────────────────────────
ChatGPT           ✗              ~            ✓             ✗            ✗
Claude             ✗              ✓            ✓             ✗            ✗
Open WebUI        ✗              ✗            ~             ✗            ✓
AnythingLLM       ✗              ~            ~             ✗            ✓
LM Studio         ✗              ✗            ✗             ✗            ✓
─────────────────────────────────────────────────────────────────────────
Kavach AI         ✓              ✓            ✓             ✓            ✓
```

## MRPL-Specific Context

**Mangalore Refinery and Petrochemicals Limited (MRPL)** is a subsidiary of ONGC, operating a 15 MMTPA refinery in Mangalore, Karnataka. Key characteristics:

1. **OISD-regulated** — All safety-critical documents follow Oil Industry Safety Directorate standards
2. **ISO 9001 / 14001 / 45001 certified** — Documented procedures for everything
3. **Thousands of P&IDs** — Each unit has hundreds of Piping & Instrument Diagrams
4. **Regular turnarounds** — Planned shutdowns generate massive inspection report volumes
5. **Internal IT team** — Has GPU server infrastructure for process simulation (Aspen HYSYS, etc.)
6. **Confidentiality-first culture** — No external cloud services for operational data

## User Pain Points (validated from PSU domain knowledge)

### Pain Point 1: Inspection Report Processing
- **Volume:** 500+ inspection reports per turnaround
- **Current time:** 2-3 hours per report to summarize and draft approval note
- **Bottleneck:** Most reports are scanned PDFs (handwritten field notes)

### Pain Point 2: Code for Internal Tools
- **Need:** Automation scripts, data extraction, format conversion
- **Barrier:** Cannot use Copilot/ChatGPT — source code contains internal system names, API keys, schema details
- **Result:** Developers work 3x slower than industry peers with AI access

### Pain Point 3: Engineering Calculations
- **Need:** Quick calculations for relief valve sizing, pipe stress, heat duty
- **Barrier:** Formulas are in internal engineering standards, not public
- **Result:** Engineers manually look up tables, compute by hand, format results

### Pain Point 4: Document Drafting
- **Need:** Approval notes, MoM, board presentations from data
- **Barrier:** Templates are internal; data is confidential
- **Result:** Hours of manual formatting and cross-referencing

## Problem Severity Assessment

| Dimension | Score (1-5) | Justification |
|---|---|---|
| **Frequency** | 5 | Every working day, across all departments |
| **Impact** | 5 | Productivity loss estimated at 20-30% of knowledge worker time |
| **Affected Population** | 5 | Every engineer, developer, officer in every PSU/refinery/defence unit |
| **Current Alternatives** | 1 | Nothing exists that is both useful AND air-gapped |
| **Urgency** | 4 | Shadow AI usage is growing; data leakage risk increases daily |
| **Feasibility** | 4 | Open-weight models have reached usable quality in 2024-2025 |

**Overall Severity: CRITICAL** — This is not a nice-to-have. It is a security-critical productivity gap affecting India's entire PSU and defence ecosystem.
