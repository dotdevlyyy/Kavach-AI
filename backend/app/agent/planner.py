"""
Kavach AI — ReAct Agent Planner
Generates initial step-by-step execution plans for complex user requests.
"""

import json
import re
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.ollama_client import ollama_client


SYSTEM_PLANNER_PROMPT = """You are Kavach AI's Strategic ReAct Agent Planner for MRPL Refinery & Critical Infrastructure operations.
Given a user's task request and optional file context, create a concise execution plan with clear steps.

Available Capabilities & Tools (use exact names for `suggested_tool`):
1. `code_execute`: Run Python code safely for data processing or math calculations.
2. `search_knowledge_base`: Query on-premise Knowledge Base for refinery SOPs, inspection standards, or P&ID data.
3. `generate_word_document`: Generate an official Word approval note (.docx).
4. `generate_excel_sheet`: Generate an Excel procurement or data spreadsheet (.xlsx).
5. `generate_presentation`: Generate a PowerPoint summary (.pptx).
6. `extract_text_from_image`: Perform OCR on scanned PDFs or images.
7. `analyze_engineering_diagram`: Analyze P&ID diagrams or engineering drawings.
8. `file_read` / `file_write`: Inspect or persist local refinery workspace files.

Respond strictly in valid JSON format:
{
    "goal": "<High-level goal statement>",
    "steps": [
        {
            "step_number": 1,
            "title": "<Short step title>",
            "description": "<What will be accomplished in this step>",
            "suggested_tool": "<tool_name or none>"
        }
    ]
}
"""


_FALLBACK_PLAN: Dict[str, Any] = {
    "goal": "",
    "steps": [
        {
            "step_number": 1,
            "title": "Analyze Task & Context",
            "description": "Gather context and execute primary logic.",
            "suggested_tool": "search_knowledge_base",
        },
        {
            "step_number": 2,
            "title": "Execute & Formulate Response",
            "description": "Synthesize results and prepare finalized output/deliverable.",
            "suggested_tool": "generate_word_document",
        },
    ],
}


def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from noisy LLM output."""
    if not text:
        return None
    # 1) Try fenced ```json ... ``` blocks first
    for fence in ("```json", "```JSON", "```"):
        if fence in text:
            try:
                body = text.split(fence, 1)[1].split("```", 1)[0].strip()
                return json.loads(body)
            except (json.JSONDecodeError, IndexError):
                continue
    # 2) Find the first balanced { ... } JSON object
    for match in re.finditer(r"\{", text):
        start = match.start()
        depth = 0
        for end in range(start, len(text)):
            if text[end] == "{":
                depth += 1
            elif text[end] == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : end + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    # 3) Last resort: strip trailing commas then parse
    cleaned = re.sub(r",\s*([\]}])", r"\1", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return None


def _normalize_plan(parsed: Dict[str, Any], task_description: str) -> Dict[str, Any]:
    """Coerce parsed JSON into the expected plan shape, fixing minor issues."""
    steps = parsed.get("steps") or []
    normalized = []
    for i, step in enumerate(steps, start=1):
        if not isinstance(step, dict):
            continue
        normalized.append({
            "step_number": step.get("step_number") or i,
            "title": step.get("title") or f"Step {i}",
            "description": step.get("description") or "",
            "suggested_tool": step.get("suggested_tool") or "none",
        })
    if not normalized:
        return {**_FALLBACK_PLAN, "goal": task_description}
    return {
        "goal": parsed.get("goal") or task_description,
        "steps": normalized,
    }


class AgentPlanner:
    """Agent planner module for generating structured step breakdown."""

    async def create_plan(
        self,
        task_description: str,
        model_name: str,
        file_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generates a structured execution plan from the user prompt."""
        user_content = f"Task Description: {task_description}"
        if file_ids:
            user_content += f"\nAttached Files: {', '.join(file_ids)}"

        messages = [
            {"role": "system", "content": SYSTEM_PLANNER_PROMPT},
            {"role": "user", "content": user_content}
        ]

        try:
            response_text = ""
            async for chunk in ollama_client.chat_stream(
                model=model_name,
                messages=messages,
                keep_alive=-1,
                options={"temperature": 0.2}
            ):
                token = chunk.message.content if hasattr(chunk, 'message') else chunk.get("message", {}).get("content", "")
                response_text += token

            parsed = _extract_json(response_text)
            if parsed is None:
                raise ValueError("No JSON object found in planner output")

            return _normalize_plan(parsed, task_description)

        except Exception as e:
            logger.warning(f"Fallback to default plan generation due to parsing error: {e}")
            return {**_FALLBACK_PLAN, "goal": task_description}


planner = AgentPlanner()
