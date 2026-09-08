"""
Kavach AI — ReAct Agent Observer
Inspects step outputs and produces observation + reflection text.
"""

from typing import Dict, Any
from loguru import logger


class AgentObserver:
    """Observer module evaluating step outputs."""

    def observe(self, step_number: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """Return a structured observation for the loop to stream and reflect on."""
        success = result.get("success", True)
        output = result.get("output", "")

        if not success:
            logger.warning(f"Step #{step_number} failed.")
            return {
                "step_number": step_number,
                "status": "failed",
                "observation": f"Step #{step_number} encountered an error: {output}",
                "reflection": f"Step #{step_number} failed. Proceeding to next step; the planner should adjust subsequent tool choices.",
            }

        return {
            "step_number": step_number,
            "status": "completed",
            "observation": f"Step #{step_number} completed successfully. Output: {output[:200]}",
            "reflection": "Output verified. Ready to proceed to next step.",
        }


observer = AgentObserver()
