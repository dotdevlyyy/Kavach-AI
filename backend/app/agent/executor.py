"""Dispatch validated agent steps to registered tools."""

import inspect
import re
from typing import Any

from loguru import logger

import app.rag.knowledge_search  # noqa: F401
import app.tools.doc_generate  # noqa: F401
import app.tools.file_read  # noqa: F401
import app.tools.file_write  # noqa: F401
import app.tools.image_analyze  # noqa: F401
import app.tools.ocr_extract  # noqa: F401
from app.tools.code_execute import execute_python_code
from app.tools.registry import _TOOL_REGISTRY, execute_tool

DOC_TOOLS = {
    "generate_word_document",
    "generate_excel_sheet",
    "generate_presentation",
    "generate_pdf_document",
}
META_KEYS = {"task", "step_title", "context", "file_id", "file_ids"}
VISION_TOOLS = {"extract_text_from_image", "analyze_engineering_diagram"}
MAX_GENERATED_TEXT_CHARS = 200_000


async def _generate_text(task: str, model: str, instruction: str) -> str:
    from app.core.ollama_client import ollama_client

    chunks = []
    total_chars = 0
    async for chunk in ollama_client.chat_stream(
        model=model,
        messages=[{"role": "user", "content": f"{instruction}\n\nRequest: {task}"}],
        keep_alive=-1,
        options={"temperature": 0.2},
    ):
        token = (
            chunk.message.content
            if hasattr(chunk, "message")
            else chunk.get("message", {}).get("content", "")
        )
        remaining = MAX_GENERATED_TEXT_CHARS - total_chars
        if remaining <= 0:
            break
        chunks.append(token[:remaining])
        total_chars += min(len(token), remaining)
        if len(token) > remaining:
            break
    return "".join(chunks).strip()


async def _document_content(task: str, context: str, model: str) -> str:
    request = task
    if context:
        request += f"\n\nVerified results from prior steps:\n{context}"
    try:
        generated = await _generate_text(
                request,
                model,
                "Write complete formatted content. Output only document content.",
            )
        generated = generated or task
        return f"{generated}\n\nSource Evidence\n{context}" if context else generated
    except Exception as exc:
        logger.warning(f"Document content generation failed: {exc}")
        return request or "No content provided."


async def _resolve_kwargs(func, tool_input: dict, model: str = "llama3.2:1b") -> dict:
    """Validate planner input and fill only documented, deterministic defaults."""
    parameters = list(inspect.signature(func).parameters.values())
    parameter_names = {parameter.name for parameter in parameters}
    values = dict(tool_input)
    if "file_path" in values and "image_path" in parameter_names:
        values["image_path"] = values.pop("file_path")
    elif "image_path" in values and "file_path" in parameter_names:
        values["file_path"] = values.pop("image_path")

    unknown = set(values) - parameter_names - META_KEYS
    if unknown:
        raise ValueError(
            f"Unknown kwargs for {func.__name__}: {sorted(unknown)}. "
            f"Declared params: {sorted(parameter_names)}"
        )

    task = str(tool_input.get("task", ""))
    context = str(tool_input.get("context", ""))
    title = str(tool_input.get("step_title", "Generated Document"))
    generated_content: str | None = None

    for parameter in parameters:
        if parameter.name in values or parameter.default is not inspect.Parameter.empty:
            continue
        if parameter.name == "title":
            values[parameter.name] = title
        elif parameter.name == "content":
            generated_content = generated_content or await _document_content(task, context, model)
            values[parameter.name] = generated_content
        elif parameter.name == "headers":
            values[parameter.name] = ["Content"]
        elif parameter.name == "rows":
            generated_content = generated_content or await _document_content(task, context, model)
            values[parameter.name] = [[generated_content]]
        elif parameter.name == "slides_content":
            generated_content = generated_content or await _document_content(task, context, model)
            values[parameter.name] = [{"title": title, "content": generated_content}]
        elif parameter.annotation in (str, inspect.Parameter.empty):
            values[parameter.name] = task or title
        else:
            raise ValueError(f"Missing required tool input: {parameter.name}")

    return {
        parameter.name: values[parameter.name]
        for parameter in parameters
        if parameter.name in values
    }


class AgentExecutor:
    async def execute_step(
        self,
        step_number: int,
        tool_name: str,
        tool_input: dict[str, Any],
        model: str = "llama3.2:1b",
    ) -> dict[str, Any]:
        logger.info(f"Executing step #{step_number} with tool: {tool_name}")
        try:
            if tool_name == "code_execute":
                code = tool_input.get("code")
                if not code:
                    code = await _generate_text(
                        str(tool_input.get("task", "")),
                        model,
                        "Write executable Python code for this request. Output code only.",
                    )
                    code = re.sub(r"^```(?:python)?\s*|\s*```$", "", code, flags=re.I)
                if not code:
                    return {
                        "tool": tool_name,
                        "success": False,
                        "output": "Unable to generate code for execution.",
                    }
                result = await execute_python_code(code=code)
                return {
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "output": result.get("output", ""),
                    "raw": result,
                }

            if tool_name in _TOOL_REGISTRY:
                func = _TOOL_REGISTRY[tool_name]
                batch_failed = False
                if tool_name in VISION_TOOLS and tool_input.get("file_ids"):
                    outputs = []
                    for file_id in tool_input["file_ids"]:
                        item_input = {**tool_input, "file_id": file_id}
                        item_input.pop("file_ids", None)
                        kwargs = await _resolve_kwargs(func, item_input, model=model)
                        item_output = str(await execute_tool(tool_name, kwargs))
                        batch_failed = batch_failed or item_output.startswith("Error")
                        outputs.append(f"[{file_id}]\n{item_output}")
                    result = "\n\n".join(outputs)
                else:
                    kwargs = await _resolve_kwargs(func, tool_input, model=model)
                    result = await execute_tool(tool_name, kwargs)
                if tool_name in DOC_TOOLS and isinstance(result, dict):
                    if result.get("status") == "ok":
                        return {
                            "tool": tool_name,
                            "success": True,
                            "output": f"Generated {result['filename']}",
                            "file_id": result["file_id"],
                            "raw": result,
                        }
                    return {
                        "tool": tool_name,
                        "success": False,
                        "output": "Document generation failed.",
                        "raw": result,
                    }

                output = str(result)
                return {
                    "tool": tool_name,
                    "success": not batch_failed and not output.startswith("Error"),
                    "output": output,
                    "raw": result,
                }

            if not tool_name or tool_name == "none":
                return {
                    "tool": "none",
                    "success": True,
                    "output": f"Step #{step_number} reasoning completed.",
                }

            return {
                "tool": tool_name,
                "success": False,
                "output": f"Unknown tool: {tool_name}",
            }
        except Exception as exc:
            logger.exception(f"Tool execution failed for {tool_name}: {exc}")
            return {
                "tool": tool_name,
                "success": False,
                "output": f"Tool execution failed: {tool_name}",
            }


executor = AgentExecutor()
