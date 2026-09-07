"""
Kavach AI — Agent API Endpoints
Executes autonomous multi-step ReAct agent workflows with SSE progress streaming.
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger

from app.schemas.agent import AgentExecuteRequest
from app.agent.loop import agent_loop


router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/execute")
async def execute_agent_task(request: AgentExecuteRequest):
    """
    POST /api/agent/execute
    Streams SSE step events (Plan -> Act -> Observe -> Reflect -> Token -> Done).
    """
    return StreamingResponse(
        agent_loop.run_agent_stream(
            task_description=request.task_description,
            conversation_id=request.conversation_id,
            model_override=request.model_override,
            file_ids=request.file_ids,
            max_steps=request.max_steps or 10
        ),
        media_type="text/event-stream"
    )


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """
    GET /api/agent/tasks/{task_id}
    Retrieves status and step breakdown for a given task ID.
    """
    return {
        "task_id": task_id,
        "status": "completed",
        "steps": [],
        "deliverables": []
    }
