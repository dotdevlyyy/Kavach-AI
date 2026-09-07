"""
Kavach AI — ReAct Agent Executor
Dispatches individual step execution requests to the Tool Registry.
"""

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


class AgentExecutor:
    """Dispatches tool execution calls based on step recommendations."""

    async def execute_step(
        self,
        step_number: int,
        tool_name: str,
        tool_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Executes a specified tool with given input arguments.
        Routes to the Tool Registry for registered tools, with special
        handling for code_execute (subprocess sandbox).
        """
        logger.info(f"Executing step #{step_number} with tool: {tool_name}")

        try:
            # Special case: code execution uses its own subprocess sandbox
            if tool_name == "code_execute":
                code = tool_input.get("code", "print('No code provided')")
                res = await execute_python_code(code=code)
                return {
                    "tool": "code_execute",
                    "success": res.get("success", False),
                    "output": res.get("output", ""),
                    "raw": res
                }

            # Check if tool is in the registry
            if tool_name in _TOOL_REGISTRY:
                result = await execute_tool(tool_name, tool_input)
                return {
                    "tool": tool_name,
                    "success": True,
                    "output": str(result)
                }

            # Default: reasoning step with no external tool call
            return {
                "tool": tool_name or "none",
                "success": True,
                "output": f"Step #{step_number} reasoning and execution completed."
            }

        except Exception as e:
            logger.error(f"Error in step #{step_number} tool execution ({tool_name}): {e}")
            return {
                "tool": tool_name,
                "success": False,
                "output": f"Error executing tool {tool_name}: {str(e)}"
            }


executor = AgentExecutor()
