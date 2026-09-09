"""
Kavach AI — ReAct Agent Executor
Dispatches individual step execution requests to the Tool Registry.
"""

import inspect
from typing import Dict, Any
from loguru import logger
from app.tools.registry import execute_tool, _TOOL_REGISTRY
from app.tools.code_execute import execute_python_code

# Import tool modules so their @register_tool decorators fire at import time
import app.tools.file_read       # noqa: F401
import app.tools.file_write      # noqa: F401
import app.tools.doc_generate    # noqa: F401
import app.tools.ocr_extract     # noqa: F401
import app.tools.image_analyze   # noqa: F401
import app.rag.knowledge_search  # noqa: F401

DOC_TOOLS = {"generate_word_document", "generate_excel_sheet", "generate_presentation", "generate_pdf_document"}


def _resolve_kwargs(func, tool_input: dict) -> dict:
    """Fill required string params from step context. Generic, no per-tool aliasing.

    Validates that every input key matches a declared parameter (after file_path↔image_path
    aliasing). Unknown keys fail loud — silent typo-swallowing let `filepath`/`file_path`
    mismatches cascade into file_read on task text. See B12.
    """
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    param_names = {p.name for p in params}
    out = dict(tool_input)

    # vision tools accept either filepath or image_path — only one is required.
    # Alias BEFORE required-str fill so an empty fill doesn't shadow the real value.
    # Drop the source key after aliasing so the unknown-key check below only sees params.
    if "file_path" in out and "image_path" not in out:
        for p in params:
            if p.name == "image_path":
                out["image_path"] = out["file_path"]
                out.pop("file_path", None)
                break
    elif "image_path" in out and "file_path" not in out:
        for p in params:
            if p.name == "file_path":
                out["file_path"] = out["image_path"]
                out.pop("image_path", None)
                break

    # Fill the first required string param from `task` / `step_title` if not provided.
    required_str = [
        p for p in params
        if p.default is inspect.Parameter.empty
        and p.annotation in (str, inspect.Parameter.empty)
    ]
    if required_str and not any(p.name in out for p in required_str):
        out[required_str[0].name] = tool_input.get("task") or tool_input.get("step_title", "")

    # Reject unknown keys — keeps the planner honest about tool signatures.
    # Meta keys (`task`, `step_title`) are agent-loop scaffolding, not planner output,
    # so they bypass the check.
    META_KEYS = {"task", "step_title"}
    unknown = set(out) - param_names - META_KEYS
    if unknown:
        raise ValueError(
            f"Unknown kwargs for {func.__name__}: {sorted(unknown)}. "
            f"Declared params: {sorted(param_names)}"
        )

    return {p.name: out[p.name] for p in params if p.name in out}


class AgentExecutor:
    """Dispatches tool execution calls based on step recommendations."""

    async def execute_step(
        self,
        step_number: int,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool call and return a normalized result dict."""
        logger.info(f"Executing step #{step_number} with tool: {tool_name}")

        try:
            if tool_name == "code_execute":
                code = tool_input.get("code", "print('Kavach AI sandbox verification successful')")
                res = await execute_python_code(code=code)
                return {
                    "tool": "code_execute",
                    "success": res.get("success", False),
                    "output": res.get("output", ""),
                    "raw": res,
                }

            if tool_name in _TOOL_REGISTRY:
                func = _TOOL_REGISTRY[tool_name]
                kwargs = _resolve_kwargs(func, tool_input)
                result = await execute_tool(tool_name, kwargs)

                # Doc tools return a dict with file_id/path/filename/status.
                # The file_id is the UUID assigned by the tool; download route
                # scans OUTPUT_DIR as a fallback (no FileUpload row created).
                if tool_name in DOC_TOOLS and isinstance(result, dict) and result.get("status") == "ok":
                    return {
                        "tool": tool_name,
                        "success": True,
                        "output": f"Generated {result['filename']}",
                        "file_id": result["file_id"],
                        "raw": result,
                    }

                # Other tools return strings
                output = str(result)
                return {
                    "tool": tool_name,
                    "success": not output.startswith("Error"),
                    "output": output,
                    "raw": result,
                }

            # Default: reasoning step with no external tool call
            return {
                "tool": tool_name or "none",
                "success": True,
                "output": f"Step #{step_number} reasoning and execution completed.",
            }

        except Exception as e:
            logger.error(f"Error in step #{step_number} tool execution ({tool_name}): {e}")
            return {
                "tool": tool_name,
                "success": False,
                "output": f"Error executing tool {tool_name}: {str(e)}",
            }


executor = AgentExecutor()

