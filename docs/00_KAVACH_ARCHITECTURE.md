# Kavach AI — System Architecture & Workflow

This document provides a comprehensive overview of the Kavach AI system architecture, technology stack, and an end-to-end simulation of the Agentic AI workflow.

---

## 1. High-Level Architecture

Kavach AI operates entirely on-premise with zero outbound network calls, ensuring 100% data sovereignty.

```mermaid
graph TD
    subgraph Frontend [Next.js 15 + Bun (localhost:3000)]
        UI[Cult UI Components]
        Chat[Agent Chat Interface]
        Sandbox[Code Sandbox Output]
        NetMon[Network Monitor]
        
        UI --> Chat
        UI --> Sandbox
        UI --> NetMon
    end

    subgraph Backend [FastAPI + UV (localhost:8000)]
        Router[Task Auto-Router]
        Agent[ReAct Agent Engine]
        RAG[RAG / Knowledge Pipeline]
        Tools[Tool Registry (8 Tools)]
        
        Router --> Agent
        Agent <--> Tools
        Agent <--> RAG
    end

    subgraph Infrastructure [Data & Models]
        DB[(SQLite + FTS5)]
        Ollama[Ollama (Local Models)]
    end

    Frontend <==>|HTTP / SSE Streaming| Backend
    Backend <==> DB
    Backend <==> Ollama
```

---

## 2. Technology Stack

Our stack is heavily optimized for local, mid-range hardware deployment without sacrificing modern capabilities.

- **Frontend:** Next.js 15 (App Router), Bun Runtime, Cult UI, Tailwind CSS.
- **Backend:** FastAPI (Python), UV (Package Manager).
- **Database:** SQLite with FTS5 (Full-Text Search). No complex external databases required.
- **AI Engine:** Ollama (running locally on port `11434`).
- **Models (Pre-loaded in 4.1GB VRAM):**
  - `llama3.2:1b` (General Chat & Summarization)
  - `qwen2.5-coder:1.5b` (Code Generation & Execution)
  - `qwen2.5vl:3b` (Vision & OCR)

---

## 3. Workflow Simulation (Request & Response)

Here is exactly what happens under the hood when a user asks Kavach AI to perform a complex task.

### Step 1: The Request
**User Input:** *"Read this attached P&ID diagram and generate a Python script to monitor these specific sensor thresholds."* (Attachment: `refinery_pid.pdf`)

### Step 2: The Router (Classification)
The backend `Task Classifier` analyzes the text and attachments in milliseconds (without an LLM).
* **Keywords detected:** "Python script", "monitor"
* **Attachments detected:** PDF image
* **Decision:** Task requires coding and vision.
* **Action:** Automatically routes to `qwen2.5-coder:1.5b` for logic and calls `qwen2.5vl:3b` for OCR.

### Step 3: The Agentic Loop (ReAct)
The Agent Engine takes over, executing a multi-step loop.

**[PLAN]**
```json
{
  "thought": "I need to extract text from the PDF, understand the thresholds, and write a Python script.",
  "steps": ["extract_text_from_image", "code_execute"]
}
```

**[ACT]**
* Calls Tool: `extract_text_from_image(file_id="pdf_123")`
* Output: *"Sensor T-101 max threshold is 450°C. Sensor P-202 max pressure is 15 bar."*

**[OBSERVE & REFLECT]**
```json
{
  "thought": "I have the thresholds. Now I will generate the Python monitoring script and test it in the sandbox.",
  "next_action": "call_tool: code_execute"
}
```

**[ACT]**
* Calls Tool: `code_execute(code="...")` 
* Output: *Script runs safely in local Docker sandbox. Returns `Exit code 0. Output: System healthy.`*

### Step 4: The Final Response
The backend streams the final response back to the Next.js frontend via Server-Sent Events (SSE).

**System Output:** 
> "I have extracted the thresholds from your diagram (T-101: 450°C, P-202: 15 bar). I have written and verified the Python monitoring script in the sandbox. You can download the script below."

---

## 4. The Knowledge Base (On-Premise RAG)

When users upload SOPs or manuals, the system uses a local RAG pipeline:
1. **Parse & Chunk:** Text is extracted and split into 512-word chunks.
2. **Embed:** Chunks are embedded using local models via Ollama.
3. **Store:** Stored in SQLite with FTS5.
4. **Search:** Uses **Hybrid Search** (Full-Text + Semantic Vector) combined via Reciprocal Rank Fusion (RRF) for highly accurate local retrieval.

---

## 5. Security & Sovereignty 

- **Air-Gapped:** The system is designed to run on a machine disconnected from the internet.
- **Local Network Monitor:** The frontend features a live dashboard utilizing `psutil` to track all socket connections, proving in real-time that `0` outbound external API calls are made.
- **Ephemeral Sandbox:** Code is executed in a read-only, non-root Docker container without network access, which is destroyed after 30 seconds.

