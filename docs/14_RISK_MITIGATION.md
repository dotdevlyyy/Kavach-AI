# 14 — Risk Mitigation & Edge Cases

## Technical Risks

### Risk 1: GPU Memory Insufficient for 3 Models

**Probability:** Medium (depends on demo hardware)
**Impact:** High — core demo feature (instant switching) broken

| Scenario | VRAM Needed | Mitigation |
|---|---|---|
| All 3 in VRAM (ideal) | ~4.1 GB | Works on any 6+ GB GPU (RTX 3060, RTX 4060) |
| 2 in VRAM + 1 CPU | ~3 GB VRAM + 1.1 GB RAM | Load llama3.2:1b on CPU (it's the smallest) |
| All on CPU | 0 GB VRAM, ~6 GB RAM | Slower but functional. Response time 5-15s. |
| No GPU at all | 0 VRAM, ~6 GB RAM | Ollama supports CPU inference. Use Q4_K_S quantization. |

**Implementation:**
```bash
# Set Ollama to allow 3 concurrent models
OLLAMA_MAX_LOADED_MODELS=3

# If VRAM is tight, reduce to 2 concurrent
OLLAMA_MAX_LOADED_MODELS=2
```

---

### Risk 2: Ollama Crashes or Hangs

**Probability:** Low-Medium
**Impact:** Critical — no AI responses

**Mitigations:**
1. Health check endpoint reports Ollama availability (`GET /api/health`)
2. Pre-warmed models loaded at startup via `preload_models()` with `keep_alive=-1` (no auto-restart of the Ollama process itself)
3. Backup plan: restart Ollama manually, takes ~20 seconds to re-warm models

```python
# app/core/ollama_client.py — startup preload
async def preload_models(self):
    for model in settings.models:
        await self.client.chat(model=model, messages=[...], keep_alive=-1)
```

---

### Risk 3: Agent Loop Gets Stuck / Infinite Loop

**Probability:** Medium (small models can lose track of multi-step plans)
**Impact:** Medium — one task fails, but system remains responsive

**Mitigations:**
1. **Hard limit:** `max_steps=10` per agent task (configurable via `AgentExecuteRequest.max_steps`)
2. **Per-step timeout:** Each LLM call wrapped in `asyncio.wait_for(..., timeout=PER_STEP_SECONDS)` — 60s
3. **Per-task timeout:** Entire agent task limited to 5 minutes — hardcoded `PER_TASK_SECONDS = 300` in `app/agent/loop.py` (no config knob; if the value needs to change, edit the constant and redeploy)
4. **Graceful degradation:** If max steps reached, return partial results with explanation
5. **Cancel button:** Frontend can POST `/api/agent/tasks/{id}/cancel` to set the cancel event; the loop's final write is authoritative for `task.status`

---

### Risk 4: Small Models Produce Low-Quality Output

**Probability:** High (1-3B models have real limitations)
**Impact:** Medium — demo looks less impressive

**Mitigations:**
1. **Curated demo scenarios:** Choose tasks where small models perform well
2. **Structured prompts:** Highly specific system prompts with formatting instructions
3. **Template-based outputs:** For document generation, the tool uses templates — the model just fills in the content sections
4. **Honest framing:** *"These are 1-3B models. The point isn't to match GPT-4 — it's that 80% quality with 100% privacy is better than 0% AI or 100% data leakage."*

**Tasks where small models excel:**
- Structured extraction (extract key findings from text)
- Code generation for common patterns (CSV parsing, data transformation)
- Summarization of structured documents
- OCR text extraction from images (Qwen2.5-VL is strong here)

**Tasks to avoid in demo:**
- Open-ended creative writing
- Complex multi-turn reasoning
- Nuanced domain-specific analysis

---

### Risk 5: Scanned PDF / OCR Quality Is Poor

**Probability:** Medium (depends on scan quality)
**Impact:** Medium — multimodal demo fails

**Mitigations:**
1. **Curated sample PDFs:** Use high-quality scanned samples, not blurry phone photos
2. **Fallback:** If OCR on scanned PDF fails, use PyMuPDF for text-based PDFs instead
3. **Page-by-page processing:** Process one page at a time to avoid context window limits

---

### Risk 6: Demo Machine Is Different From Dev Machine

**Probability:** High (SIH venues often provide machines)
**Impact:** Critical — nothing works

**Mitigations:**
1. **Bring your own laptop:** Primary option
2. **Portable setup script:** `setup.ps1` / `setup.sh` that installs everything
3. **Pre-vendored dependencies:**
   - Backend: `uv sync` creates reproducible environment from lockfile
   - Frontend: `bun install` from lockfile
   - Models: Pre-downloaded Ollama models on USB drive
4. **Backup laptop:** Second team member carries identical setup
5. **Backup video:** Pre-recorded demo in PPT file

---

### Risk 7: Network Monitor Shows Unexpected External Connections

**Probability:** Low (but embarrassing if it happens)
**Impact:** Critical — destroys the sovereignty claim

**Mitigations:**
1. **Disable all auto-updates:** Windows Update, browser sync, antivirus cloud scan
2. **Disable telemetry:** Next.js telemetry off, Python telemetry off
3. **Firewall rules:** Block all outbound except localhost in Windows Firewall
4. **Test beforehand:** Run network monitor for 10 minutes with all services running, verify zero external
5. **Explanation ready:** If something shows up (e.g., NTP time sync), explain it's OS-level and not from the application

```bash
# Disable Next.js telemetry
npx next telemetry disable

# Block all outbound (Windows Firewall)
netsh advfirewall set allprofiles firewallpolicy blockinbound,blockoutbound
# Then allow localhost
netsh advfirewall firewall add rule name="Allow Localhost" dir=out action=allow remoteip=127.0.0.1
```

---

## Operational Risks

### Risk 8: Team Member Unavailable

**Mitigation:** Each component has a primary AND secondary owner. No single point of failure.

| Component | Primary | Secondary |
|---|---|---|
| Backend API | Backend 1 | Backend 2 |
| Agent Engine | Backend 2 | Backend 1 |
| Model Router | Backend 1 | Lead |
| Chat UI | Frontend 1 | Frontend 2 |
| Network Monitor | Frontend 2 | Frontend 1 |
| Demo Script | Lead | Design |

---

### Risk 9: Time Overrun (10-day plan slips)

**Priority cut order (what to drop if behind):**

| Priority | Feature | Drop Impact |
|---|---|---|
| P0 (must have) | Basic chat + model auto-selection | Cannot demo without |
| P0 (must have) | At least 1 agentic task end-to-end | PS requirement |
| P0 (must have) | Network monitor (sovereignty proof) | PS requirement |
| P1 (important) | File upload + vision/OCR | Multimodal demo |
| P1 (important) | Code sandbox execution | Code task demo |
| P2 (nice to have) | Knowledge base + RAG | Can be faked with hardcoded context |
| P2 (nice to have) | Document generation (DOCX/XLSX) | Can show text output instead |
| P3 (polish) | Task history page | Not required for demo |
| P3 (polish) | Settings page | Not required for demo |
| P3 (polish) | Fancy animations / transitions | Demo works without |

---

### Risk 10: Judges Ask About Scalability

**Prepared answer:**
> *"This is designed as a single-server, single-organization deployment — which is exactly what an air-gapped system needs to be. For multi-user scaling, we would:
> 1. Add Ollama load balancing (multiple instances behind nginx)
> 2. Switch SQLite → PostgreSQL for concurrent writes
> 3. Add user authentication via LDAP/AD integration (PSUs already have this)
> 4. Deploy on the org's existing GPU cluster
> But for the SIH demo and the core use case — one organization, one server, maximum data sovereignty — single-server is the correct architecture."*

---

## Edge Cases

| Edge Case | Handling |
|---|---|
| User uploads 100 MB PDF | Reject with error: "Max file size: 20 MB" |
| User uploads non-supported format (.exe, .zip) | Reject with error: "Unsupported file type" |
| User types in Hindi/regional language | Llama 3.2 has basic Hindi support. Response may be mixed Hindi-English. Known limitation. |
| Empty message sent | Pydantic rejects it with HTTP 422 and a validation-error body. |
| Agent tool throws exception | Catch, log, return tool error to agent. Agent can retry or skip. |
| Code sandbox runs dangerous code (rm -rf) | Execution fails closed unless a Docker CLI, daemon, and pre-provisioned `python:3.13-slim` image are available. Container uses no network, read-only root, non-root user, dropped capabilities, `no-new-privileges`, 512 MB memory, 1 CPU, 64 PIDs, 30s timeout, and 1 MB live output caps. Never mount an unrestricted host Docker socket into the public API container. |
| SQLite database gets corrupted | Startup enables WAL, `synchronous=NORMAL`, and foreign keys. Backups and restore verification are operator-managed; the backend does not schedule backups. |
| Required Ollama model missing | Startup never downloads. Provision all four models offline; health reports `installed`, `loaded`, and `ready` per model and becomes unhealthy when a required model is absent. |
| Browser refresh during streaming | Frontend re-fetches conversation from DB. Stream is lost but history preserved. |
| Two browser tabs sending messages simultaneously | SQLite WAL mode handles concurrent reads. Writes are serialized but fast. |
