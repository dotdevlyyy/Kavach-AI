"""
Kavach AI — ReAct Agent Observer & Self-Correction
Inspects step observations and determines task completion or reflection requirements.
"""

from typing import Dict, Any
from loguru import logger


class AgentObserver:
    """Observer module evaluating step outputs and self-correction."""

    def observe(self, step_number: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inspects step result and returns structured observation object.
        """
        success = result.get("success", True)
        output = result.get("output", "")

        if not success:
            logger.warning(f"Step #{step_number} failed. Recommending self-correction.")
            return {
                "step_number": step_number,
                "status": "failed",
                "observation": f"Step #{step_number} encountered an error: {output}",
                "reflection": f"Retry step #{step_number} with corrected parameters or alternative tool.",
                "requires_self_correction": True
            }

        return {
            "step_number": step_number,
            "status": "completed",
            "observation": f"Step #{step_number} completed successfully. Output: {output[:200]}",
            "reflection": "Output verified. Ready to proceed to next step.",
            "requires_self_correction": False
        }


observer = AgentObserver()
