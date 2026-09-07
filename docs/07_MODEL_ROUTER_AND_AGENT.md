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

def get_all_models() -> list[str]:
    """Return all unique models in the routing table."""
    return list(set(ROUTING_TABLE.values()))
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

```python
# app/agent/loop.py
from ollama import AsyncClient
from app.tools.registry import ToolRegistry
from app.router.router import get_model_for_task
from app.schemas.common import TaskType, StepType

AGENT_SYSTEM_PROMPT = """You are Kavach AI, a sovereign on-premise AI assistant.
You help industrial users with tasks by planning and using tools.

Available tools:
{tool_descriptions}

When you need to use a tool, respond with:
TOOL_CALL: tool_name(param1="value1", param2="value2")

When you are done with the task, respond with:
TASK_COMPLETE: <summary of what was accomplished>

Think step by step. After each tool result, reflect on whether you have enough
information to complete the task or need additional steps.
"""

class AgentLoop:
    def __init__(self, ollama_client: AsyncClient, tool_registry: ToolRegistry):
        self.client = ollama_client
        self.tools = tool_registry
        self.max_steps = 10
    
    async def execute(self, task_description: str, files: list[str], max_steps: int = 10):
        """Execute an agentic task. Yields steps as they happen."""
        
        self.max_steps = max_steps
        messages = []
        
        # System prompt with tool descriptions
        system_prompt = AGENT_SYSTEM_PROMPT.format(
            tool_descriptions=self.tools.get_descriptions()
        )
        messages.append({"role": "system", "content": system_prompt})
        
        # User task
        task_message = f"Task: {task_description}"
        if files:
            task_message += f"\n\nAvailable files: {', '.join(files)}"
        messages.append({"role": "user", "content": task_message})
        
        step_number = 0
        
        while step_number < self.max_steps:
            step_number += 1
            
            # Determine model based on current context
            task_type = self._infer_task_type(messages)
            model = get_model_for_task(task_type)
            
            # Get LLM response
            response = await self.client.chat(
                model=model,
                messages=messages,
                keep_alive=-1,
            )
            
            content = response.message.content
            
            # Check if task is complete
            if "TASK_COMPLETE:" in content:
                summary = content.split("TASK_COMPLETE:")[-1].strip()
                yield {
                    "step_number": step_number,
                    "type": StepType.REFLECT,
                    "content": summary,
                    "model_used": model,
                    "is_final": True,
                }
                break
            
            # Check for tool calls
            if "TOOL_CALL:" in content:
                # Parse tool call
                tool_name, tool_input = self._parse_tool_call(content)
                
                # Yield the action step
                yield {
                    "step_number": step_number,
                    "type": StepType.ACT,
                    "content": content,
                    "model_used": model,
                    "tool_call": {"tool_name": tool_name, "tool_input": tool_input},
                }
                
                # Execute tool
                tool_result = await self.tools.execute(tool_name, tool_input)
                
                # Yield tool result
                yield {
                    "step_number": step_number,
                    "type": StepType.OBSERVE,
                    "content": f"Tool '{tool_name}' returned:\n{tool_result}",
                    "tool_result": tool_result,
                }
                
                # Add to conversation
                messages.append({"role": "assistant", "content": content})
                messages.append({"role": "user", "content": f"Tool result:\n{tool_result}"})
            else:
                # Pure reasoning step (plan or reflect)
                step_type = StepType.PLAN if step_number == 1 else StepType.REFLECT
                yield {
                    "step_number": step_number,
                    "type": step_type,
                    "content": content,
                    "model_used": model,
                }
                messages.append({"role": "assistant", "content": content})
        
        # If max steps reached without completion
        if step_number >= self.max_steps:
            yield {
                "step_number": step_number,
                "type": StepType.REFLECT,
                "content": "Maximum steps reached. Task may be incomplete.",
                "is_final": True,
                "status": "max_steps_reached",
            }
```

### Tool Registry

```python
# app/tools/registry.py
from typing import Callable, Any

class Tool:
    def __init__(self, name: str, description: str, parameters: dict, handler: Callable):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, Tool] = {}
    
    def register(self, name: str, description: str, parameters: dict, handler: Callable):
        self._tools[name] = Tool(name, description, parameters, handler)
    
    async def execute(self, tool_name: str, tool_input: dict) -> str:
        if tool_name not in self._tools:
            return f"Error: Unknown tool '{tool_name}'"
        tool = self._tools[tool_name]
        try:
            result = await tool.handler(**tool_input)
            return str(result)
        except Exception as e:
            return f"Error executing {tool_name}: {str(e)}"
    
    def get_descriptions(self) -> str:
        lines = []
        for tool in self._tools.values():
            params_str = ", ".join(f'{k}: {v}' for k, v in tool.parameters.items())
            lines.append(f"- {tool.name}({params_str}): {tool.description}")
        return "\n".join(lines)
```

### Available Tools

| Tool | Parameters | Description |
|---|---|---|
| `file_read` | `file_path: str` | Read contents of a file from workspace |
| `file_write` | `file_path: str, content: str` | Write content to a file |
| `code_execute` | `code: str, language: str` | Execute code in sandboxed subprocess |
| `doc_generate` | `type: str, content: dict` | Generate DOCX/XLSX/PPTX document |
| `knowledge_search` | `query: str, top_k: int` | Search local knowledge base |
| `ocr_extract` | `file_id: str` | Extract text from scanned image/PDF via Qwen2.5-VL |
| `image_analyze` | `file_id: str, question: str` | Analyze image and answer question via Qwen2.5-VL |

### Code Sandbox (Tool Detail)

```python
# app/tools/code_execute.py
import subprocess
import tempfile
import os

async def execute_code(code: str, language: str = "python") -> str:
    """Execute code in a sandboxed subprocess."""
    
    if language != "python":
        return f"Error: Only Python execution is supported"
    
    # Create temp directory for isolation
    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = os.path.join(tmpdir, "script.py")
        
        with open(script_path, "w") as f:
            f.write(code)
        
        try:
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=30,          # 30 second timeout
                cwd=tmpdir,          # Isolated working directory
                env={                # Minimal environment
                    "PATH": os.environ.get("PATH", ""),
                    "PYTHONPATH": "",
                },
            )
            
            output = ""
            if result.stdout:
                output += f"STDOUT:\n{result.stdout}\n"
            if result.stderr:
                output += f"STDERR:\n{result.stderr}\n"
            if result.returncode != 0:
                output += f"Exit code: {result.returncode}\n"
            
            return output or "Code executed successfully (no output)"
            
        except subprocess.TimeoutExpired:
            return "Error: Code execution timed out (30s limit)"
```

### Document Generation (Tool Detail)

```python
# app/tools/doc_generate.py
from docx import Document as DocxDocument
from openpyxl import Workbook
from pptx import Presentation
import os

async def generate_document(doc_type: str, content: dict) -> str:
    """Generate a document (DOCX, XLSX, or PPTX)."""
    
    output_dir = "./data/outputs"
    os.makedirs(output_dir, exist_ok=True)
    
    if doc_type == "docx":
        return _generate_docx(content, output_dir)
    elif doc_type == "xlsx":
        return _generate_xlsx(content, output_dir)
    elif doc_type == "pptx":
        return _generate_pptx(content, output_dir)
    else:
        return f"Error: Unsupported document type '{doc_type}'"

def _generate_docx(content: dict, output_dir: str) -> str:
    doc = DocxDocument()
    
    if "title" in content:
        doc.add_heading(content["title"], 0)
    
    if "sections" in content:
        for section in content["sections"]:
            if "heading" in section:
                doc.add_heading(section["heading"], level=1)
            if "body" in section:
                doc.add_paragraph(section["body"])
            if "table" in section:
                table_data = section["table"]
                table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                for i, row in enumerate(table_data):
                    for j, cell in enumerate(row):
                        table.cell(i, j).text = str(cell)
    
    filename = f"{content.get('filename', 'document')}.docx"
    filepath = os.path.join(output_dir, filename)
    doc.save(filepath)
    return f"Generated: {filepath}"
```

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
