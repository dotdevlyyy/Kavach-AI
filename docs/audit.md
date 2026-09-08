# Ponytail Audit Report — Kavach AI (post-merge)

**Date:** 2026-09-08
**Mode:** Ponytail `ponytail-audit` (repo-wide, ranked biggest-cut-first)
**Scope:** Over-engineering, complexity, dead code, speculative features, duplication.
**Out of scope:** correctness bugs, security, performance. (Separate review pass.)

Format per finding: `<tag> <what>. <replacement>. [path]`.
Ranked by lines + dependencies removable, biggest cut first.

---

## Tier 1 — biggest cuts

### `delete` `frontend/components/agent/RoutingWorkflowModal.tsx` (148 LOC)
A static decorative modal showing "Start Workflow → Classify Query → Route: General / Refund / Technical → Complete" with hardcoded references to `gpt-4o-mini`, `o4-mini`, `deepseek/deepseek-v4-flash-0731`, "Expert customer service agent", "Refund specialist", "Refund requests", "Technical support".

This codebase is an MRPL refinery workbench with on-prem Ollama models (`llama3.2:1b`, `qwen2.5-coder:1.5b`, `qwen2.5vl:3b`). The modal describes a customer-service agent that has zero overlap with the actual product. Wrong-project leftover.

Replacement: delete the file + the trigger on `app/page.tsx` (line 52). [frontend/components/agent/RoutingWorkflowModal.tsx, frontend/app/page.tsx:23,52]

### `delete` Duplicate `StreamConsumer` — pick one
Two files do the same job:

- `frontend/lib/StreamConsumer.ts` (81 LOC) — function-based, **currently imported** by `app/chat/page.tsx:8`.
- `frontend/components/chat/StreamConsumer.ts` (89 LOC) — class-based, **zero importers**.

Replacement: delete the orphan. The class-based version is also worse (`any` types, constructor with 4 callbacks instead of one event callback). Keep the function. [frontend/components/chat/StreamConsumer.ts]

### `delete` Dead Python deps in `pyproject.toml` (still)
Three declared deps remain unused after merge:

- `Pillow>=10.0.0` — no `from PIL` / `import PIL` anywhere.
- `sse-starlette>=2.0.0` — never imported; `StreamingResponse` already covers SSE.
- `tzdata` — never imported.

`psutil`, `PyMuPDF` (`fitz`), and `python-docx` are now used by `api/network.py` and `rag/parser.py`. Drop those first three only.

Replacement: nothing. [backend/pyproject.toml, backend/Dockerfile]

### `delete` Dead models — still zero callers
- `ToolCall` (`backend/app/models/tool_call.py`) — no `ToolCall.create/.filter/.get/.all` anywhere.
- `NetworkLog` (`backend/app/models/network_log.py`) — same.

Replacement: drop files, remove from `models/__init__.py` `__all__` and `TORTOISE_ORM["models"]` in `core/database.py`. [backend/app/models/tool_call.py, backend/app/models/network_log.py, backend/app/models/__init__.py, backend/app/core/database.py:24-34]

### `delete` `Document` model still has no creator
`Document` is read in `rag/pipeline.py:22` (`await Document.get_or_none(id=document_id)`), but no API endpoint ever creates one. `FileUpload` is what `/api/files/upload` writes. The whole `parser → chunker → pipeline → Document` chain has no entry from HTTP. `test_ingestion.py` calls `parse_document` + `chunk_text` directly to verify them in isolation.

Pick one:
- (a) Drop `Document` and rewrite `pipeline.py` to ingest straight from `FileUpload`, OR
- (b) Add `/api/knowledge/ingest` that takes a `file_id`, chunks, embeds, and creates `Document` + `KnowledgeChunk` rows.

Today: half-wired. Replacement: ship (a) OR (b), not both half-done. [backend/app/models/document.py, backend/app/rag/pipeline.py, backend/app/rag/parser.py, backend/app/rag/chunker.py]

### `delete` Frontend cosmetic bloat
Two files with one consumer each, zero functional value:

- `frontend/components/ui/sonar-grid.tsx` (261 LOC) — bespoke canvas engine (rAF loop, three observers, ring physics) used only on `app/network/page.tsx` for a background animation behind the audit table.
- `frontend/components/ui/GlareHover.tsx` (111 LOC) — hand-rolled hex→rgba + overlay animation, used 3× on `app/page.tsx` for dashboard cards.

Replacement: drop `SonarGrid` wrapper; plain `<div>`. Replace `GlareHover` with a Tailwind `hover:border-primary/50 transition-colors` on the cards themselves (already wrapped around them). [frontend/components/ui/sonar-grid.tsx, frontend/components/ui/GlareHover.tsx, frontend/app/page.tsx, frontend/app/network/page.tsx]

### `delete` Unused msgspec Struct schemas (still)
Eleven Structs defined, none imported:

- `schemas/chat.py`: `ChatMetadataEvent`, `ChatTokenEvent`, `ChatDoneEvent`, `ConversationSummary`, `MessageResponse`, `ConversationDetail`.
- `schemas/agent.py`: `AgentTaskCreatedEvent`, `AgentStepEvent`, `AgentToolResultEvent`, `AgentDoneEvent`, `AgentTaskDetail`.

Endpoints emit raw `dict` literals via `json.dumps`. Replacement: delete the Structs, keep only the request models (`ChatRequest`, `AgentExecuteRequest`). [backend/app/schemas/chat.py:21-79, backend/app/schemas/agent.py:21-68]

---

## Tier 2 — large simplifies

### `delete` `core/config.py:load_settings()` 30-line env-var boilerplate
Manual `if "X" in os.environ: kwargs["X"] = ...` ladder for 13 settings. All read once at startup; Dockerfile hardcodes the values.

Replacement: either drop env wiring entirely (constants only), or use `pydantic-settings.BaseSettings` (5 lines). [backend/app/core/config.py:53-81]

### `yagni` `AgentPlanner` / `AgentObserver` / `AgentExecutor` classes with module singletons
Three classes, one method each, no instance state. `AgentLoop` is the sole consumer.

Replacement: bare functions. Drop the classes. [backend/app/agent/planner.py, backend/app/agent/observer.py, backend/app/agent/executor.py]

### `yagni` `executor.py` 7-branch kwargs remap + `TOOL_ALIASES` dict
Lines 57-99 hand-map `tool_input` dict → typed kwargs per tool. The registry already knows each tool's signature.

Replacement: `inspect.signature(tool).bind(**kwargs)` (with required-fields check) + planner emits registry names directly. Delete the dict + ladder. [backend/app/agent/executor.py:20-25, 57-99]

### `yagni` `tools/registry.py` docstring parser + `_TOOL_SCHEMAS`
`parse_docstring` walks lines for `Args:` format; `get_type_name` is a 4-line reimplementation of what `inspect.signature(...).parameters[name].annotation` gives you. `_TOOL_SCHEMAS` is built but `get_all_tool_schemas()` has no caller.

Replacement: keep the bare dict registry; build schema on demand from `inspect.signature` if/when LLM-tool-calling surface ships. [backend/app/tools/registry.py:1-87]

### `delete` `core/msgspec_adapter.py`
Custom `Response` subclass for one endpoint (`api/files.py:84,94`) + `decode_request()` no one calls.

Replacement: inline `JSONResponse(content=msgspec.json.encode(content))`. Delete the file. [backend/app/core/msgspec_adapter.py, backend/app/api/files.py]

### `delete` Dead helpers in `core/ollama_client.py`
- `preload_all_models` — alias for `preload_models`, never called.
- `preloaded_models` property — never read.
- `list_models` — never called.

Replacement: keep `preload_models`, `chat`, `chat_stream`, `embed`, `is_healthy`. Delete the rest. [backend/app/core/ollama_client.py:82-84, 151-192, 211-214]

### `delete` Dead router state
- `MODEL_INFO` (router.py:44-66) — never queried.
- `get_all_models` (router.py:81-83) — never called.

Replacement: nothing. Delete. [backend/app/router/router.py:44-83]

### `delete` `Settings.app_name` property
Returns `self.APP_NAME`, never called.

Replacement: drop the property. [backend/app/core/config.py:48-50]

### `delete` Dead model fields on live tables (still)
- `Message.tokens_in`, `Message.tokens_out`, `Message.latency_ms`, `Message.task_type`, `Message.model_used`, `Message.files`.
- `Conversation.metadata`, `Conversation.model_override`, `Conversation.system_prompt`.
- `FileUpload.conversation` FK — never set.
- `AgentStep.tool_calls`, `AgentStep.tokens_used`, `AgentStep.duration_ms`, `AgentStep.model_used`.
- `AgentTask.completed_at` — never set; status is the source of truth.
- `Document.mime_type`, `Document.file_type`, `Document.file_size` — moot if Document is dropped.

Replacement: drop the columns. [backend/app/models/message.py, conversation.py, file_upload.py, agent_step.py, agent_task.py]

### `shrink` Merge `tools/ocr_extract.py` + `tools/image_analyze.py`
Both: read file, base64-encode, call `qwen2.5vl:3b` chat with images. Only the prompt differs.

Replacement: one `vision_query(path: str, prompt: str) -> str`. Planner picks prompt. [backend/app/tools/ocr_extract.py, backend/app/tools/image_analyze.py]

### `shrink` `chat/page.tsx` keyword sniff for agent routing
`isAgentTask = message.toLowerCase().includes("plan") || message.toLowerCase().includes("execute")` decides between `/api/chat` and `/api/agent/execute`. Fragile — "explain how to plan a vacation" trips agent mode.

Replacement: explicit UI toggle ("Agent mode on/off"), not string sniffing. [frontend/app/chat/page.tsx:68-72]

### `shrink` `chat/page.tsx` step-type shim
Line 89 maps `"action"`→`"act"`, `"observation"`→`"observe"`, `"reflection"`→`"reflect"`. Backend (`agent/loop.py:111,123,140`) sends canonical names already.

Replacement: delete the shim. [frontend/app/chat/page.tsx:89]

### `shrink` `api/chat.py` duplicates user message in history
Persists user message at line 38-42, then loads last 20 at line 72-74 (which includes the just-persisted one), and pushes all into the LLM context. User message appears twice every turn.

Replacement: load history BEFORE persisting, or filter out the just-saved one. [backend/app/api/chat.py:72-78]

### `shrink` `api/chat.py` no-op title update
```python
if conversation.title == request.message[:80] and full_response:
    conversation.title = request.message[:80]
    await conversation.save()
```
Sets title to the value it just compared against.

Replacement: delete the block. [backend/app/api/chat.py:98-101]

### `shrink` `api/chat.py` ignores request `system_prompt`
`ChatRequest.system_prompt` accepted, hardcoded prompt used instead.

Replacement: drop the field, or honor it. [backend/app/schemas/chat.py:17, backend/app/api/chat.py:64-69]

### `shrink` `agent/loop.py` `requires_self_correction` is a label, not behavior
Observer sets the flag, loop emits a string event, proceeds as if nothing failed. Misleading.

Replacement: implement retry or remove the flag. [backend/app/agent/observer.py:27, backend/app/agent/loop.py:164-166]

### `shrink` Embedder: `struct.pack` → `array.array`
`serialize_embedding` / `deserialize_embedding` use `struct.pack(f"{n}f", ...)`. Stdlib `array` does this.

Replacement:
```python
import array
def serialize_embedding(v): return array.array('f', v).tobytes()
def deserialize_embedding(b): return array.array('f', b).tolist()
```
[backend/app/rag/embedder.py:27-35]

### `yagni` CORS regex + tuple double-cover
`allow_origins=tuple(...)` + `allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?"`. Tuple already names localhost; regex adds nothing.

Replacement: pick one. Drop the regex. [backend/app/main.py:48-55]

### `yagni` Duplicate root + health endpoints
`GET /` returns `{"app","version","status","air_gapped"}`. `GET /api/health` returns the same plus Ollama check.

Replacement: drop `/`. [backend/app/main.py:63-72]

### `yagni` `topbar.tsx` "Secure Logout"
Toast says "Secure Logout Initiated", comment says `// Real logout logic goes here`. No auth in app.

Replacement: drop the dropdown until auth ships. [frontend/components/shared/Topbar.tsx:24-30, 89-97]

### `yagni` `frontend/lib/utils.ts`
One line: `export { cn } from "cn"`.

Replacement: delete; import `cn` from `cn` directly. [frontend/lib/utils.ts]

### `yagni` `frontend/app/settings/page.tsx`
Static placeholder + `{/* @Pritam: Wire up to GET /api/models */}`. No fetch.

Replacement: implement the page or delete it. [frontend/app/settings/page.tsx]

### `yagni` `frontend/app/knowledge/page.tsx` dialog has no handlers
`<input type="file">` no `onChange`; "Ingest & Embed" button no `onClick`. No backend `/api/knowledge/ingest` either.

Replacement: ship both ends or delete the dialog. [frontend/app/knowledge/page.tsx:32-46]

### `yagni` `frontend/components.json` + `shadcn`
`shadcn` is a CLI generator, declared as runtime `dependencies`. UI primitives were hand-written against `@base-ui/react`, not shadcn-generated.

Replacement: move `shadcn` to `devDependencies` (or remove); drop `components.json` if unused. [frontend/components.json, frontend/package.json]

### `yagni` `core/database.py` `_enable_global_fallback=True`
Tortoise fallback that swallows typos in `.filter()` calls.

Replacement: remove. [backend/app/core/database.py:53]

### `yagni` `core/database.py` `init_fts5()` references dead `Document`
Creates triggers on `knowledge_chunks` and `documents` tables. `Document` is never populated; triggers fire on every cold start and log warnings. Pure noise. (If you ship `Document` per Tier 1, re-evaluate.)

Replacement: drop `init_fts5()` until ingest is wired. [backend/app/core/database.py:54-91]

### `native` Frontend `zustand` `persist` duplicates server conversations
`useChatStore` keeps chats in `localStorage` via `persist`. Server already stores conversations in `Conversation` + `Message` tables. Multi-device users see different histories; the chat list on the sidebar is stale.

Replacement: fetch `/api/chat/conversations` on mount; drop `persist`. [frontend/lib/store.ts:32-105, frontend/components/shared/Sidebar.tsx:23-27, 86-128]

### `native` `GlareHover` hand-rolled hex→rgba parser
Lines 38-50. If kept, `Color(value).withAlpha(opacity)` from any color lib. Better: delete the file. [frontend/components/ui/GlareHover.tsx]

### `native` `frontend/components/shared/Topbar.tsx` custom click-outside dropdown
Manual `mousedown` outside-click. The project already has `@base-ui/react/menu`. Or use native `<details>`.

Replacement: native or `@base-ui/react`. [frontend/components/shared/Topbar.tsx:14-22]

### `delete` `frontend/public/*.svg` boilerplate
`file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, `window.svg` — Next.js starter SVGs. None imported.

Replacement: nothing. [frontend/public/]

### `delete` `frontend/app/favicon.ico` (25 KB default)
Default Next.js favicon. Replace with a 1 KB asset or accept the default.

Replacement: ship when branded. [frontend/app/favicon.ico]

---

## Tier 3 — small wins + reuse

### `shrink` `MessageBubble.tsx` heavy code rendering
`react-syntax-highlighter` + `vscDarkPlus` (Prism) for every code block. Big bundle, slow on long chats.

Replacement: `rehype-highlight` inside the existing `react-markdown`, or accept defaults. [frontend/components/chat/MessageBubble.tsx:3-7, 59-67]

### `shrink` `FileUploadZone.tsx` 90 LOC for a styled `<input type=file multiple>`
Drag/drop, file list, remove buttons, click-to-browse — all for a native input element.

Replacement: plain `<input type="file" multiple onChange={...} className="..." />`. ~10 LOC. [frontend/components/chat/FileUploadZone.tsx]

### `shrink` `api/files.py` `get_file_type`
Hand-rolled ext→type switch. `mimetypes.guess_type` is already imported but ignored for the ext path.

Replacement: one source of truth (ext or mime, not both). [backend/app/api/files.py:29-44]

### `yagni` `rag/retriever.py` `search_fts` icontains fallback
Falls back to `KnowledgeChunk.filter(content__icontains=query)` — full table scan, no index. The fallback is the only path that actually runs today (no embeddings exist). Marked "production fallback".

Replacement: drop the fallback, raise on miss. [backend/app/rag/retriever.py:45-57]

### `yagni` `rag/retriever.py` `search_vector` brute-force cosine
Loads up to 200 chunks, deserializes each embedding, computes cosine in pure Python.

Replacement: add `ponytail:` comment naming the ceiling + upgrade path. Or drop until embeddings exist. [backend/app/rag/retriever.py:60-104]

### `yagni` `chat.py` welcome message embedded in store
`createChat()` seeds a hardcoded welcome paragraph into the first message ("I am connected securely to the MRPL air-gapped network..."). Belongs on the server.

Replacement: have server return a default first reply; drop the embedded welcome. [frontend/lib/store.ts:42-51]

### `delete` `backend/test_integration.py` + `backend/test_ingestion.py`
Two bare-script test files at `backend/` root. No pytest, no CI wiring, different patterns (one uses `starlette.testclient`, other prints to stdout).

Replacement: pick one runner (`pytest`), one location (`backend/tests/`). Or move under `scripts/`. [backend/test_integration.py, backend/test_ingestion.py]

---

## Code reuse + duplication

### `duplicate` Two `StreamConsumer` files
Already covered in Tier 1.

### `duplicate` SSE event formatter
Both `api/chat.py` and `agent/loop.py` construct SSE strings manually: `f"event: {type}\ndata: {json.dumps(payload)}\n\n"`. Five-plus call sites.

```python
def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
```
[backend/app/api/chat.py, backend/app/agent/loop.py]

### `duplicate` Routing metadata dict
`api/chat.py:54-61` and `agent/loop.py:52-58` build near-identical `{"conversation_id", "model", "task_type", "confidence"/no, "reasoning"}` dicts. Field names diverge (`task_type` vs both). `RoutingMetadata` msgspec struct exists for this.

Replacement: serialise the existing `RoutingMetadata`. [backend/app/api/chat.py:54-61, backend/app/agent/loop.py:52-58, backend/app/schemas/common.py:64-69]

### `duplicate` `chunk_text` shadowing
`rag/chunker.py:16` exports `chunk_text`. `rag/pipeline.py:28` iterates with `chunk_text` as the loop variable. Name collision — works but the import is shadowed inside the loop body. Rename the loop var or import alias.

Replacement: `for i, text in enumerate(text_chunks):`. [backend/app/rag/chunker.py:16, backend/app/rag/pipeline.py:28-35]

### `duplicate` `DATA_DIR` resolution in three tools
`tools/file_read.py:5`, `tools/file_write.py:5`, `tools/image_analyze.py:6`, `tools/ocr_extract.py:6` all do `Path("data").resolve() if Path("data").exists() else Path("backend/data").resolve()`. Plus `api/files.py:22-26` does the same for `UPLOAD_DIR` and `OUTPUT_DIR`.

Replacement: one `paths.py` with `DATA_ROOT = next(p for p in (Path("data"), Path("backend/data")) if p.exists()).resolve()`. [backend/app/tools/file_read.py:5, file_write.py:5, image_analyze.py:6, ocr_extract.py:6, backend/app/api/files.py:22-26]

### `duplicate` `models/list[] → API` serialization
`api/chat.py`, `api/agent.py`, `api/files.py` each hand-write `[{...} for x in model]` serializers. `msgspec.to_builtins` covers this.

Replacement: define the response Struct, `msgspec.to_builtins(items)`. [backend/app/api/chat.py:115-145, backend/app/api/agent.py:39-82, backend/app/api/files.py:48-119]

### `yagni` `ConversationSummary` + `ConversationDetail` Structs in `schemas/chat.py`
Both defined, never returned. Endpoint returns inline dicts. (Already covered in dead-schema delete; flag here because they're a duplicate-of-design — if any endpoint ever returns conversations, use one Struct, not two.) [backend/app/schemas/chat.py]

---

## Files safe to delete entirely

```
backend/app/models/tool_call.py
backend/app/models/network_log.py
backend/app/models/document.py         # OR wire ingest; pick one
backend/app/core/msgspec_adapter.py
backend/app/schemas/chat.py            # keep only ChatRequest
backend/app/schemas/agent.py          # keep only AgentExecuteRequest
frontend/components/agent/RoutingWorkflowModal.tsx
frontend/components/ui/sonar-grid.tsx
frontend/components/ui/GlareHover.tsx
frontend/components/chat/FileUploadZone.tsx
frontend/components/chat/StreamConsumer.ts   # orphan class
frontend/lib/utils.ts
frontend/public/{file,globe,next,vercel,window}.svg
docs/                                  # collapse into top-level README
```

## Net estimate

| Bucket | Approx. |
|---|---|
| Backend LOC removed | -550 |
| Frontend LOC removed | -700 |
| Python deps removed | -3 (Pillow, sse-starlette, tzdata) |
| Dead tables / models dropped | -3 (ToolCall, NetworkLog, Document\*) |
| Dead model columns dropped | ~14 |
| Dead Struct schemas dropped | -11 |
| Duplicate SSE / metadata formatters | -2 helpers unified |
| Duplicate `DATA_DIR` resolution | -5 sites → 1 |

\* `Document` drop contingent on Tier 1 decision.

**Net: -1,250 LOC, -3 deps possible.**

---

## Post-merge regression check (what was wrong in the prior audit)

The prior audit said these were dead. They aren't anymore:

| Was flagged dead | Now used by |
|---|---|
| `psutil` | `backend/app/api/network.py` |
| `PyMuPDF` (`fitz`) | `backend/app/rag/parser.py` |
| `python-docx` (`docx`) | `backend/app/rag/parser.py` |
| `next-themes` | `frontend/components/theme-provider.tsx`, `AnimatedThemeToggler.tsx` |

Findings the prior audit missed:

- **Wrong-project leftover** — `RoutingWorkflowModal.tsx` (customer-service GPT workflow, not refinery).
- **Duplicate StreamConsumer** — class + function for the same job, one is orphan.
- **`Document` model half-wired** — parser/chunker/pipeline exist, no API endpoint drives them.
- **Misleading retry label** — `requires_self_correction` doesn't retry.
- **`chat.py` history loop duplicates user message** every turn.
- **No-op title update** in `chat.py`.
- **`DATA_DIR` resolved five different times** in tools + api.
- **SSE formatter duplicated** across endpoints.