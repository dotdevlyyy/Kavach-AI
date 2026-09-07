"""
Kavach AI — ReAct Agent Planner
Generates initial step-by-step execution plans for complex user requests.
"""

import json
from typing import List, Dict, Any, Optional
from loguru import logger
from app.core.ollama_client import ollama_client


SYSTEM_PLANNER_PROMPT = """You are Kavach AI's Strategic ReAct Agent Planner for MRPL Refinery & Critical Infrastructure operations.
Given a user's task request and optional file context, create a concise execution plan with clear steps.

Available Capabilities & Tools:
1. `code_execute`: Run Python code safely for data processing or math calculations.
2. `knowledge_search`: Query on-premise Knowledge Base for refinery SOPs, inspection standards, or P&ID data.
3. `doc_generate`: Generate official Word approval notes (.docx) or Excel procurement spreadsheets (.xlsx).
4. `ocr_extract`: Perform OCR and visual document parsing on scanned PDFs or images.
5. `file_read` / `file_write`: Inspect or persist local refinery workspace files.

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
                options={"temperature": 0.2}
            ):
                response_text += chunk

            # Parse JSON plan from response
            cleaned_text = response_text.strip()
            if "```json" in cleaned_text:
                cleaned_text = cleaned_text.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_text:
                cleaned_text = cleaned_text.split("```")[1].split("```")[0].strip()

            plan_data = json.loads(cleaned_text)
            return plan_data

        except Exception as e:
            logger.warning(f"Fallback to default plan generation due to parsing error: {e}")
            return {
                "goal": task_description,
                "steps": [
                    {
                        "step_number": 1,
                        "title": "Analyze Task & Context",
                        "description": f"Gather context and execute primary logic for: {task_description[:100]}",
                        "suggested_tool": "knowledge_search"
                    },
                    {
                        "step_number": 2,
                        "title": "Execute & Formulate Response",
                        "description": "Synthesize results and prepare finalized output/deliverable.",
                        "suggested_tool": "doc_generate"
                    }
                ]
            }


planner = AgentPlanner()
