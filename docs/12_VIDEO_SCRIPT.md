# 12 — Video Script

> **Duration:** 3-5 minutes
> **Format:** Screen recording with voiceover
> **Resolution:** 1920x1080, 30fps
> **Tool:** OBS Studio

---

## Scene 1: Title Card (10 seconds)

**Visual:** Animated Kavach AI logo on dark background

**Text on screen:**
```
KAVACH AI (कवच)
Sovereign On-Premise Agentic AI Workbench
PS 26117 | MRPL | SIH 2026
```

---

## Scene 2: The Problem (30 seconds)

**Visual:** Stock footage / illustration of refinery + office workers + lock/shield icons

**Voiceover:**
> *"Every day, thousands of engineers in India's refineries, PSUs, and defence units do knowledge work — drafting approval notes, writing code, reviewing inspection reports, analyzing engineering drawings. This work is critical, and the data behind it is confidential.*
>
> *But today, they face a dilemma. Cloud AI tools like ChatGPT and Copilot can help — but company policy forbids uploading confidential data to external servers. So they either work manually, losing hours of productivity... or they quietly paste sensitive data into public AI tools, creating a data leakage risk no one talks about."*

---

## Scene 3: The Solution (20 seconds)

**Visual:** Kavach AI dashboard — show all 3 models loaded, green health indicators

**Voiceover:**
> *"Kavach AI solves this. It's a fully self-hosted, air-gapped AI workbench that runs entirely on the organization's own server. Three specialized open-weight models — for chat, code, and vision — all preloaded in GPU memory for instant switching. Nothing ever leaves the premises."*

---

## Scene 4: Model Auto-Selection Demo (40 seconds)

**Visual:** Screen recording of chat UI

**Action 1:** Type general question → Show model badge "llama3.2:1b"
**Action 2:** Type coding question → Show model badge switches to "qwen2.5-coder:1.5b"
**Action 3:** Upload image → Show model badge switches to "qwen2.5vl:3b"

**Voiceover:**
> *"The system automatically picks the right model for each task. Ask a general question — it routes to Llama. Ask for code — it switches to Qwen Coder. Upload an image — it activates Qwen Vision. No manual selection needed. The router classifies the task type in real-time using keyword analysis and file type detection."*

---

## Scene 5: Agentic Workflow Demo (60 seconds)

**Visual:** Screen recording of agent executing the inspection report task

**Action:** Upload scanned inspection report → Type task → Watch agent steps unfold

**Voiceover:**
> *"Here's where Kavach goes beyond a chatbot. We upload a scanned inspection report — this is a real scenario in any refinery. The AI plans the task, calls OCR to extract text from the scanned document, analyzes the findings, searches the organization's knowledge base for relevant SOP sections, and generates a complete Word approval note.*
>
> *This entire workflow — which would take an engineer two to three hours manually — completes in under a minute. And the output is a real, downloadable Word document with proper formatting."*

**Show:** Download and open the generated DOCX file

---

## Scene 6: Code Sandbox Demo (30 seconds)

**Visual:** Screen recording of code generation + execution

**Action:** Ask for a Python script → Code generated → Click "Run in Sandbox" → Output displayed

**Voiceover:**
> *"For trusted-host development, Kavach can execute generated code in a locked-down disposable Docker container with no network and strict resource limits. The shipped backend container leaves this optional capability disabled."*

---

## Scene 7: Vision + Multimodal Demo (30 seconds)

**Visual:** Screen recording of P&ID analysis

**Action:** Upload P&ID drawing → AI identifies equipment and instrumentation

**Voiceover:**
> *"P&ID diagrams are among the most sensitive documents in a refinery. Kavach's vision model can analyze these drawings on-device — identifying equipment, control valves, and instrumentation — without the drawing ever leaving the organization's network."*

---

## Scene 8: Sovereignty Proof (30 seconds)

**Visual:** Network Monitor page showing all connections are local

**Action:** Show live connections → Point out "External: 0" → Optionally show Wireshark

**Voiceover:**
> *"And here's the proof of the sovereign claim. The network monitor shows every single connection made during this entire demo. Every one is between localhost processes — frontend to backend, backend to Ollama. Zero external IP addresses. Zero DNS lookups. Zero port 443 traffic. This isn't a statement on a slide — it's live network data."*

---

## Scene 9: Closing (20 seconds)

**Visual:** Summary slide → Kavach AI logo

**Text on screen:**
```
✓ 3 models, auto-selected per task
✓ True agentic execution with tools
✓ Multimodal: scanned docs, drawings, images
✓ Real outputs: DOCX, XLSX, PPTX, working code
✓ Zero external network calls — provable
✓ 4.1 GB VRAM — runs on any mid-range GPU
```

**Voiceover:**
> *"Kavach AI — three models, three purposes, zero cloud calls. Sovereign AI for India's industrial backbone. Thank you."*

---

## Production Notes

- **Recording software:** OBS Studio (free, open-source)
- **Resolution:** 1920x1080 at 30fps
- **Audio:** External microphone preferred, record in quiet room
- **Browser:** Maximize the browser window, hide bookmarks bar
- **Font size:** Increase browser zoom to 125% for readability
- **Speed:** Type slowly during demos, pause after each result
- **Editing:** Cut pauses > 2 seconds, add subtle zoom on key elements
- **Export:** MP4 with H.264 codec, < 100 MB for SIH portal upload
- **Backup:** Also export as WebM for cross-platform compatibility
