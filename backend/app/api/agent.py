"""
Kavach AI — Agent API Endpoints
Executes autonomous multi-step ReAct agent workflows with SSE progress streaming.
"""

import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.agent.loop import agent_loop
from app.core.cancellation import registry as cancel_registry
from app.models.agent_step import AgentStep
from app.models.agent_task import AgentTask
from app.schemas.agent import AgentExecuteRequest
from app.schemas.responses import ActionResponse, TaskResponse, TasksResponse

router = APIRouter(prefix="/api/agent", tags=["Agent"])


@router.post(
    "/execute",
    response_class=StreamingResponse,
    responses={200: {"content": {"text/event-stream": {}}}},
)
async def execute_agent_task(request: AgentExecuteRequest):
    """
    POST /api/agent/execute
    Streams SSE step events (Plan -> Act -> Observe -> Reflect -> Token -> Done).
    """
    file_ids = list(
        dict.fromkeys(str(file_id) for file_id in [*request.file_ids, *request.files])
    )
    if file_ids:
        from app.core.uploads import AGENT_ATTACHMENT_TYPES, UploadLimitError, resolve_uploads

        try:
            await resolve_uploads(file_ids, AGENT_ATTACHMENT_TYPES)
        except UploadLimitError as exc:
            raise HTTPException(status_code=413, detail=str(exc))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
    conversation_id = str(request.conversation_id or uuid.uuid4())
    task_id = str(uuid.uuid4())
    cancel_event = cancel_registry.get(task_id)

    async def event_stream():
        try:
            async for event in agent_loop.run_agent_stream(
                task_description=request.task_description,
                conversation_id=conversation_id,
                model_override=request.model_override,
                system_prompt=request.system_prompt,
                file_ids=file_ids,
                max_steps=request.max_steps,
                cancel_event=cancel_event,
                task_id=task_id,
            ):
                yield event
        finally:
            cancel_registry.clear(task_id)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/tasks", response_model=TasksResponse)
async def list_tasks(limit: int = Query(default=20, ge=1, le=100)):
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
        "total": await AgentTask.all().count(),
    }


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_details(task_id: UUID):
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


@router.post("/tasks/{task_id}/cancel", response_model=ActionResponse)
async def cancel_task(task_id: UUID):
    """
    POST /api/agent/tasks/{id}/cancel
    Signal cancellation for a running task. Idempotent.
    The loop's final write is authoritative for task.status; this handler only signals.
    """
    key = str(task_id)
    task = await AgentTask.get_or_none(id=key)
    if not cancel_registry.contains(key):
        if task:
            return {"status": "not_running", "task_id": key}
        raise HTTPException(status_code=404, detail="Task not found")

    cancel_registry.cancel(key)
    return {"status": "cancellation_signaled", "task_id": key}
