# 10 — Demo Script

> **Duration:** 8-10 minutes
> **Format:** Live demo on a single workstation/laptop with mid-range GPU

## Pre-Demo Setup

Before the demo starts:
1. Ollama running with all 3 models preloaded (`ollama ps` shows all 3)
2. Backend running (`uv run uvicorn app.main:app`)
3. Frontend running (`bun run dev`)
4. Network monitor visible (or Wireshark open in background)
5. Sample files ready: scanned inspection report, P&ID drawing, code task
6. Knowledge base pre-loaded with 2-3 sample SOPs

---

## Demo Flow

### Opening (30 seconds)

> *"Good morning, judges. We are Team [Name], and we present Kavach AI — a sovereign, air-gapped AI workbench for confidential industrial work. The entire system runs on this single machine. No cloud. No internet. Nothing leaves the premises."*

**Show:** Dashboard page with:
- All 3 models showing as loaded (green indicators)
- System health: all green
- Network monitor badge: "0 External Connections"

---

### Demo 1: Model Auto-Selection (2 minutes)

**Objective:** Show that the router picks the right model for different tasks.

**Step 1:** Type a general question:
> *"What are the standard safety precautions during a refinery turnaround?"*

**Point out:** Model badge shows "llama3.2:1b" was auto-selected for general chat.

**Step 2:** Type a coding question:
> *"Write a Python function that reads a CSV file and calculates the average pressure readings from columns 'P1' and 'P2', handling missing values."*

**Point out:** Model badge changes to "qwen2.5-coder:1.5b" — the system detected code keywords and automatically routed to the code-specialized model.

**Talking point:**
> *"Notice the model badge — the system automatically detected this is a coding task and routed it to Qwen2.5-Coder, which is purpose-built for code. No manual model selection needed. The router uses keyword analysis and heuristics to classify tasks in real-time."*

---

### Demo 2: Agentic Task — Inspection Report to Approval Note (3 minutes)

**Objective:** Full end-to-end agentic workflow with multiple steps, tool use, and document generation.

**Step 1:** Switch to agent mode. Upload `inspection_report.pdf` (a sample scanned inspection report).

**Step 2:** Type the task:
> *"Read this inspection report, extract the key findings, and draft an approval note as a Word document."*

**Watch the agent work:**

- **Step 1 (Plan):** Agent explains its plan — "I'll extract text from the scanned PDF, identify key findings, and generate an approval note."
- **Step 2 (Act):** Agent calls `ocr_extract` tool → Qwen2.5-VL processes the scanned PDF
- **Step 3 (Observe):** Agent reviews extracted text, identifies findings (corrosion at elbow E-204, thinning at shell course S-3)
- **Step 4 (Act):** Agent calls `knowledge_search` to find relevant SOP sections
- **Step 5 (Act):** Agent calls `doc_generate` to create a Word document
- **Step 6 (Reflect):** Agent confirms task is complete

**Step 3:** Download the generated Word document. Open it to show:
- Proper formatting with heading, date, subject
- Key findings section with extracted data
- Recommendation section
- Approval signature block

**Talking point:**
> *"This is what we mean by 'agentic' — the AI didn't just answer a question. It planned the work, called multiple tools, processed a scanned document through OCR, searched our knowledge base for context, and produced a real Word document. This would take an engineer 2-3 hours manually."*

---

### Demo 3: Coding Task in Sandbox (1.5 minutes)

**Objective:** Show code generation, execution, and iteration.

**Step 1:** Type:
> *"Write a Python script that generates a summary report from this sample data: {'Unit': 'CDU-2', 'Inspection_Date': '2025-03-15', 'Defects_Found': 7, 'Critical': 2, 'Status': 'Action Required'}. Format the output as a table and calculate the defect severity ratio."*

**Step 2:** AI generates Python code using Qwen2.5-Coder.

**Step 3:** Click "Run in Sandbox" button. Show:
- Code executing in isolated subprocess
- Output displayed in the chat (formatted table + calculations)
- No external network calls made during execution

**Talking point:**
> *"The code runs in a sandboxed environment — isolated subprocess with timeout and memory limits. This is critical for a secure environment where arbitrary code execution needs to be contained."*

---

### Demo 4: Multimodal — P&ID Drawing Analysis (1.5 minutes)

**Objective:** Show vision model understanding an engineering drawing.

**Step 1:** Upload a sample P&ID drawing (PNG/JPG).

**Step 2:** Ask:
> *"Analyze this P&ID drawing. Identify the major equipment, control valves, and instrumentation shown."*

**Step 3:** Qwen2.5-VL processes the image and provides:
- Equipment identification (pumps, heat exchangers, vessels)
- Control valve locations
- Instrument tag numbers visible

**Point out:** Model badge shows "qwen2.5vl:3b" — vision model auto-selected because an image was uploaded.

**Talking point:**
> *"P&ID diagrams are some of the most sensitive documents in a refinery. They show the entire process flow. Today, engineers can't use cloud AI to analyze these. With Kavach, they can — because nothing leaves this machine."*

---

### Demo 5: Sovereignty Proof (1 minute)

**Objective:** Prove zero external network calls.

**Step 1:** Navigate to the Network Monitor page.

**Step 2:** Show the live connections table:
- `127.0.0.1:3000 ↔ 127.0.0.1:8000` (frontend ↔ backend) ✅ Local
- `127.0.0.1:8000 ↔ 127.0.0.1:11434` (backend ↔ Ollama) ✅ Local
- **No external IPs. No port 443. No DNS lookups.**

**Step 3:** Show the "External Connections: 0" counter that has been tracking throughout the entire demo.

**Optional:** If Wireshark is available, show the capture — zero packets to external IPs.

**Talking point:**
> *"This is the actual proof of the sovereign claim. Not a statement in a slide — real network data showing that throughout this entire demo, every single connection was between localhost processes. Nothing went outside. This is the guarantee that MRPL, or any PSU, needs before they can trust an AI system with their confidential data."*

---

### Closing (30 seconds)

> *"Kavach AI — three models, three purposes, zero cloud calls. Everything runs here. The models are preloaded at startup and stay in memory for instant switching. New models can be added without redesigning the system. And the outputs are real — Word documents, Excel files, working code — not just chat text. Thank you."*

---

## Anticipated Judge Questions

| Question | Answer |
|---|---|
| "How do you add new models?" | Pull via Ollama, add to routing table config. No code change needed for standard additions. |
| "What if the GPU is too small?" | All 3 models fit in ~4 GB VRAM. CPU fallback is available. We can also run 2 models in VRAM and 1 on CPU. |
| "How does it compare to ChatGPT quality?" | These are 1-3B parameter models — they won't match GPT-4. But they're genuinely useful for structured tasks (report drafting, code, OCR). The trade-off is sovereignty: 80% quality with 100% data privacy. |
| "Can it handle 100 users?" | Current design is single-user/single-server. For multi-user, we'd scale Ollama horizontally and add user auth. The architecture supports it. |
| "Why not vLLM instead of Ollama?" | Ollama is simpler to deploy (single binary), supports model management, and is sufficient for single-server. vLLM would be used for production multi-GPU scaling. |
| "Why SQLite not Postgres?" | Zero-setup deployment. No extra service. FTS5 gives us full-text search. For a single-server on-premise deployment, SQLite is the right choice. |
| "Why msgspec not Pydantic?" | 10-50x faster serialization, 3x less memory. In a constrained on-premise environment, performance matters. Trade-off: slightly more integration work with FastAPI. |
| "What about data at rest encryption?" | SQLite supports SEE (SQLite Encryption Extension). For the demo, we focus on network isolation. Encryption at rest is a production addition. |
| "How do you handle hallucinations?" | RAG grounding with citations. The AI cites which source document each claim comes from. Users can verify. |

## Fallback Plan

If live demo fails:
1. Pre-recorded video (5 minutes) covers all 5 demo scenarios
2. Embedded in PPT as a backup
3. Presenter switches to video with: *"Let me show you a recording of the system in action"*
