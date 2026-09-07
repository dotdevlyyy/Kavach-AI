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
from app.models.agent_task import AgentTask
from app.models.agent_step import AgentStep


router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post("/execute")
async def execute_agent_task(request: AgentExecuteRequest):
    """
    POST /api/agent/execute
    Streams SSE step events (Plan -> Act -> Observe -> Reflect -> Token -> Done).
    """
    file_ids = request.file_ids or request.files
    return StreamingResponse(
        agent_loop.run_agent_stream(
            task_description=request.task_description,
            conversation_id=request.conversation_id,
            model_override=request.model_override,
            file_ids=file_ids,
            max_steps=request.max_steps or 10
        ),
        media_type="text/event-stream"
    )


@router.get("/tasks")
async def list_tasks(limit: int = 20):
    """GET /api/agent/tasks — List recent agent tasks."""
    tasks = await AgentTask.all().order_by("-created_at").limit(limit)
    return {
        "tasks": [
            {
                "id": str(t.id),
                "description": t.description,
                "status": t.status,
                "total_steps": t.total_steps,
                "created_at": str(t.created_at),
            }
            for t in tasks
        ],
        "total": await AgentTask.all().count()
    }


@router.get("/tasks/{task_id}")
async def get_task_details(task_id: str):
    """GET /api/agent/tasks/{task_id} — Retrieves status and step breakdown."""
    task = await AgentTask.get_or_none(id=task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    steps = await AgentStep.filter(agent_task=task).order_by("step_number")
    return {
        "task_id": str(task.id),
        "description": task.description,
        "status": task.status,
        "total_steps": task.total_steps,
        "created_at": str(task.created_at),
        "steps": [
            {
                "step_number": s.step_number,
                "type": s.type,
                "content": s.content,
                "created_at": str(s.created_at),
            }
            for s in steps
        ],
    }
