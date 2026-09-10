# 07 — Model Router & Agent Engine

## Part 1: Model Auto-Selection Router

### Overview

The Model Router is the core differentiator — it automatically picks the right open-weight model for each user request. No manual model switching required.

```
User Message → Task Classifier → Routing Table → Ollama (correct model)
```

### Task Classification Strategy

We use a **keyword + heuristic classifier** (not an LLM classifier — that would add latency). The classifier examines the user's message, attached files, and conversation context to determine the task type.

```python
# app/router/classifier.py
import re
from app.schemas.common import TaskType

# Keyword sets for classification
CODE_KEYWORDS = {
    "code", "function", "class", "debug", "error", "bug", "script",
    "python", "javascript", "typescript", "java", "sql", "html", "css",
    "api", "endpoint", "database", "query", "algorithm", "regex",
    "compile", "syntax", "variable", "loop", "array", "dict",
    "import", "install", "pip", "npm", "git", "docker",
    "refactor", "optimize", "test", "unittest", "pytest",
    "def ", "class ", "return ", "if __name__",
    "```python", "```js", "```sql", "```bash",
}

VISION_KEYWORDS = {
    "image", "photo", "picture", "drawing", "diagram", "scan",
    "scanned", "p&id", "pid", "isometric", "blueprint", "sketch",
    "handwritten", "photograph", "screenshot", "chart", "graph",
    "what do you see", "describe this", "read this", "extract from",
    "ocr", "recognize", "identify in",
}

DOCUMENT_KEYWORDS = {
    "draft", "write a", "compose", "prepare", "create a note",
    "approval note", "memo", "letter", "report", "presentation",
    "word doc", "docx", "excel", "xlsx", "pptx", "powerpoint",
    "template", "format", "generate document",
}

SUMMARIZE_KEYWORDS = {
    "summarize", "summary", "key points", "main findings",
    "brief", "overview", "tldr", "highlights", "gist",
    "condense", "distill",
}

def classify_task(
    message: str,
    has_images: bool = False,
    has_pdfs: bool = False,
    file_types: list[str] | None = None,
) -> TaskType:
    """Classify user message into a task type for model routing."""
    
    message_lower = message.lower().strip()
    file_types = file_types or []
    
    # Rule 1: If images are attached, it's a vision task
    if has_images:
        return TaskType.VISION
    
    # Rule 2: If scanned PDFs are attached and user asks about content
    if has_pdfs and any(kw in message_lower for kw in {"read", "extract", "scan", "ocr", "what"}):
        return TaskType.OCR
    
    # Rule 3: Check for code-related keywords
    code_score = sum(1 for kw in CODE_KEYWORDS if kw in message_lower)
    vision_score = sum(1 for kw in VISION_KEYWORDS if kw in message_lower)
    doc_score = sum(1 for kw in DOCUMENT_KEYWORDS if kw in message_lower)
    summarize_score = sum(1 for kw in SUMMARIZE_KEYWORDS if kw in message_lower)
    
    # Rule 4: Check for code blocks in message
    if "```" in message or re.search(r'def\s+\w+|class\s+\w+|import\s+\w+', message):
        code_score += 5
    
    # Rule 5: Highest score wins
    scores = {
        TaskType.CODE_GENERATION: code_score,
        TaskType.VISION: vision_score,
        TaskType.DOCUMENT_DRAFT: doc_score,
        TaskType.SUMMARIZATION: summarize_score,
    }
    
    max_type = max(scores, key=scores.get)
    max_score = scores[max_type]
    
    if max_score >= 2:
        return max_type
    
    # Default to general chat
    return TaskType.GENERAL_CHAT
```

### Routing Table

```python
# app/router/router.py
from app.schemas.common import TaskType

ROUTING_TABLE: dict[TaskType, str] = {
    # General purpose tasks → Llama 3.2 (best general reasoning at 1B)
    TaskType.GENERAL_CHAT:      "llama3.2:1b",
    TaskType.SUMMARIZATION:     "llama3.2:1b",
    TaskType.DOCUMENT_DRAFT:    "llama3.2:1b",
    
    # Code tasks → Qwen2.5-Coder (specialized for code)
    TaskType.CODE_GENERATION:   "qwen2.5-coder:1.5b",
    TaskType.CODE_REVIEW:       "qwen2.5-coder:1.5b",
    TaskType.CODE_DEBUG:        "qwen2.5-coder:1.5b",
    
    # Vision/OCR tasks → Qwen2.5-VL (multimodal)
    TaskType.VISION:            "qwen2.5vl:3b",
    TaskType.OCR:               "qwen2.5vl:3b",
    TaskType.DOCUMENT_ANALYSIS: "qwen2.5vl:3b",
    
    # Spreadsheet (uses code model to generate processing code)
    TaskType.SPREADSHEET:       "qwen2.5-coder:1.5b",
    
    # Unknown defaults to general
    TaskType.UNKNOWN:           "llama3.2:1b",
}

def get_model_for_task(task_type: TaskType) -> str:
    """Return the model name for a given task type."""
    return ROUTING_TABLE.get(task_type, "llama3.2:1b")
```

### Model Routing Metadata (sent to frontend)

Every response includes a `ModelBadge` so the user knows which model was auto-selected:

```python
class RoutingMetadata(msgspec.Struct):
    task_type: str          # "code_generation"
    model_selected: str     # "qwen2.5-coder:1.5b"
    confidence: float       # 0.85 (based on keyword score)
    reasoning: str          # "Detected code keywords: 'function', 'python', 'debug'"
```

---

## Part 2: Agent Engine (ReAct Loop)

### Overview

The Agent Engine implements a **ReAct (Reasoning + Acting)** loop that enables multi-step task execution with tool use.

```
┌──────────────────────────────────────────────┐
│                 AGENT LOOP                    │
│                                              │
│   ┌───────┐    ┌───────┐    ┌──────────┐    │
│   │ PLAN  │───►│  ACT  │───►│ OBSERVE  │    │
│   │       │    │       │    │          │    │
│   │ What  │    │ Call  │    │ Check    │    │
│   │ steps │    │ tool  │    │ output   │    │
│   │ needed│    │       │    │          │    │
│   └───┬───┘    └───────┘    └────┬─────┘    │
│       │                          │           │
│       │    ┌──────────────┐     │           │
│       │    │   REFLECT    │◄────┘           │
│       │    │              │                  │
│       │    │ Is task done?│                  │
│       │    │ Need more    │                  │
│       │    │ steps?       │                  │
│       │    └──────┬───────┘                  │
│       │           │                          │
│       │     ┌─────▼─────┐                    │
│       │     │  DONE? ───►  YES → Return     │
│       │     │           │                    │
│       │     │  NO ──────►  Loop back        │
│       │     └───────────┘                    │
│       │           │                          │
│       └───────────┘                          │
│                                              │
│   Max iterations: 10 (configurable)          │
│   Timeout: 5 minutes per task                │
└──────────────────────────────────────────────┘
```

### Agent Loop Implementation

The loop lives on the module-level `AgentLoop` instance in `app/agent/loop.py`. Each step emits SSE
events; the planner returns JSON, the executor dispatches via the tool registry, the observer
generates a reflection, and a final token stream summarises the result.

```python
# app/agent/loop.py (canonical shape)
async def run_agent_stream(
    task_description: str,
    conversation_id: str | None = None,
    file_ids: list[str] = [],
    max_steps: int = 10,
    cancel_event: asyncio.Event | None = None,
) -> AsyncGenerator[str, None]:
    """Yields SSE-formatted strings: metadata, step, tool_result, token, done."""

    # 1. Routing
    selected_model, route_metadata = await route_request(...)

    # 2. ReAct loop: execute the bounded plan
    successful_results = []
    for step_idx, plan in enumerate(plan_steps, start=1):
        if cancelled():
            break
        plan.tool_input["context"] = bounded(successful_results)
        act = await executor.execute_step(step_idx, plan.tool, plan.tool_input)
        if act.success:
            successful_results.append(act.output)
        obs = await observer.observe(act)
        yield sse("step", {"type": "act"|"observe"|"reflect", "step": step_idx, ...})

    # 3. Final synthesis + done event
```

Each successful result contributes at most 4,000 characters to a 16,000-character rolling
context. Document generation uses that evidence, not only the original request. Planner-selected
attachment IDs must belong to the request. A fallback OCR step processes every attached ID.

Timeouts (intentionally hardcoded as constants in the loop; no config knob — edit `app/agent/loop.py` and redeploy if a value needs to change):
- `PER_TASK_SECONDS = 300` (5 min total)
- `PER_STEP_SECONDS = 60` (per-step `asyncio.wait_for` ceiling)

### Tool Registry

The registry is a flat dict with a decorator-based registration pattern, not a class hierarchy:

```python
# app/tools/registry.py
_TOOL_REGISTRY: dict[str, Callable] = {}

def register_tool(name: str):
    def decorator(func):
        _TOOL_REGISTRY[name] = func
        return func
    return decorator

async def execute_tool(name: str, kwargs: dict) -> Any:
    func = _TOOL_REGISTRY[name]
    if inspect.iscoroutinefunction(func):
        return await func(**kwargs)
    return func(**kwargs)
```

Usage in a tool module:

```python
# app/tools/file_read.py
@register_tool("file_read")
def file_read(file_path: str) -> str:
    """Read sandboxed file. Returns content or error string."""
    ...
```

Tools register themselves at import time; `app/agent/executor.py` imports each tool module so the decorators fire at startup. The planner prompt's tool list is hard-coded in `app/agent/planner.py:13-38` (no dynamic `get_descriptions()`).

`code_execute` is not advertised to the default planner because the shipped backend container has
no secure runner connection. The implementation remains available for explicit operator testing
when the backend runs directly on a trusted host with Docker.

### Available Tools

| Tool | Parameters | Description |
|---|---|---|
| `file_read` | `file_path: str` | Read at most 1 MB from `data/workspace` |
| `file_write` | `file_path: str, content: str` | Create a file up to 1 MB in `data/workspace`; never overwrite |
| `code_execute` | `code: str` | Optional Docker sandbox for trusted operator deployments |
| `generate_word_document` | `title, content, author?` | Generate DOCX |
| `generate_excel_sheet` | `title, headers, rows` | Generate XLSX with formula-safe text cells |
| `generate_presentation` | `title, slides_content` | Generate PPTX |
| `generate_pdf_document` | `title, content, author?` | Generate PDF; unsupported font glyphs return an error |
| `search_knowledge_base` | `query: str` | Search local knowledge base |
| `extract_text_from_image` | `file_id: str` | Extract text from image/PDF via Qwen2.5-VL |
| `analyze_engineering_diagram` | `file_id: str, query: str` | Analyze engineering image |

### Code Sandbox (Tool Detail)

`code_execute` never runs generated code in the backend host process. It requires a reachable
Docker daemon, Docker CLI, and a pre-provisioned local `python:3.13-slim` image. If any prerequisite
is missing, it returns `Secure code sandbox unavailable` and does not fall back.

Each run uses a named, disposable container with `--network none`, a read-only root filesystem,
non-root UID/GID, all capabilities dropped, `no-new-privileges`, 512 MB memory, 1 CPU, 64 PIDs,
a 16 MB `noexec` tmpfs, and only a read-only script mount. Runtime is capped at 30 seconds.
stdout and stderr are each capped at 1 MB while streaming. Cleanup runs in `finally`, including
timeout and caller cancellation.

The default backend image does not expose a Docker daemon, so this capability is unavailable there.
Production deployments that enable it must use a separately secured runner boundary. Do not mount
an unrestricted host Docker socket into an internet- or user-facing backend container.

### Document Generation (Tool Detail)

Four registered tools own generation: `generate_word_document(title, content, author?)`,
`generate_excel_sheet(title, headers, rows)`, `generate_presentation(title, slides_content)`, and
`generate_pdf_document(title, content, author?)`. Each returns `status`, a UUID `file_id`,
`filename`, and output `path` on success. XLSX formula-like text is escaped. PDF accepts characters
present in the bundled font, excluding scripts that require shaping, including Arabic, Devanagari,
and Kannada. Unsupported text returns an error instead of silently dropping glyphs.

## Part 3: Model Preloading at Startup

### FastAPI Lifespan

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from ollama import AsyncClient
from tortoise import Tortoise
from app.core.config import settings
from app.core.database import TORTOISE_ORM
import logging

logger = logging.getLogger(__name__)

MODELS_TO_PRELOAD = [
    "llama3.2:1b",
    "qwen2.5-coder:1.5b", 
    "qwen2.5vl:3b",
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: init DB, pull models, preload into VRAM."""
    
    # 1. Initialize database
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    logger.info("✅ Database initialized")
    
    # 2. Initialize Ollama client
    client = AsyncClient(host=settings.ollama_host)
    app.state.ollama = client
    
    # 3. Pull and preload models
    for model_name in MODELS_TO_PRELOAD:
        logger.info(f"📦 Pulling model: {model_name}")
        try:
            await client.pull(model_name)
            logger.info(f"✅ Model pulled: {model_name}")
        except Exception as e:
            logger.warning(f"⚠️ Model already available or pull failed: {e}")
        
        # Warm up — load into VRAM with keep_alive=-1 (never unload)
        logger.info(f"🔥 Warming up model: {model_name}")
        await client.chat(
            model=model_name,
            messages=[{"role": "user", "content": "hi"}],
            keep_alive=-1,  # CRITICAL: Keep in memory forever
        )
        logger.info(f"✅ Model loaded and warm: {model_name}")
    
    # 4. Verify all models are loaded
    ps = await client.ps()
    loaded = [m.model for m in ps.models] if ps.models else []
    logger.info(f"🧠 Models in VRAM: {loaded}")
    
    yield  # Application runs
    
    # Shutdown
    await Tortoise.close_connections()
    logger.info("🔒 Shutdown complete")

app = FastAPI(
    title="Kavach AI",
    description="Sovereign On-Premise Agentic AI Workbench",
    version="1.0.0",
    lifespan=lifespan,
)
```

### Ollama keep_alive Behavior

| `keep_alive` value | Behavior |
|---|---|
| `"5m"` (default) | Model unloaded after 5 minutes of inactivity |
| `"1h"` | Unloaded after 1 hour |
| `-1` | **Never unloaded** — stays in VRAM until Ollama restarts |
| `0` | Unloaded immediately after response |

We use `keep_alive=-1` for all three models to ensure **instant switching** with zero cold-start latency.

### Concurrent Model Loading

Ollama supports loading multiple models simultaneously if sufficient VRAM is available. With our 3 small models (~4.1 GB total), this works on any 6+ GB GPU. For CPU-only systems, models are loaded into system RAM instead.

To configure Ollama for concurrent models:
```bash
# Environment variable (set before starting ollama serve)
OLLAMA_NUM_PARALLEL=3
OLLAMA_MAX_LOADED_MODELS=3
```
