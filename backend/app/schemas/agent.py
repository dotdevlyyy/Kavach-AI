"""
Kavach AI — Agent Request/Response Schemas
msgspec Structs for the /api/agent endpoints.
"""

import msgspec


class AgentExecuteRequest(msgspec.Struct):
    """Request body for POST /api/agent/execute."""
    task_description: str
    conversation_id: str | None = None
    files: list[str] = []
    max_steps: int = 10
    enable_knowledge_base: bool = True


class AgentTaskCreatedEvent(msgspec.Struct):
    """SSE event when an agent task is created."""
    task_id: str
    status: str


class AgentStepEvent(msgspec.Struct):
    """SSE event for each agent step."""
    step_number: int
    type: str  # "plan", "act", "observe", "reflect"
    content: str
    model_used: str | None = None
    tool_call: dict | None = None
    is_final: bool = False


class AgentToolResultEvent(msgspec.Struct):
    """SSE event for a tool execution result."""
    step_number: int
    tool_name: str
    tool_output: str
    status: str  # "success" | "error"
    duration_ms: int = 0
    file_id: str | None = None


class AgentDoneEvent(msgspec.Struct):
    """SSE event when agent task completes."""
    task_id: str
    status: str  # "completed" | "failed" | "max_steps_reached"
    total_steps: int
    output_files: list[str] = []
    result_summary: str = ""


class AgentTaskDetail(msgspec.Struct):
    """Full detail of an agent task with steps."""
    id: str
    description: str
    status: str
    plan: list = []
    result_summary: str | None = None
    output_files: list[str] = []
    total_steps: int = 0
    max_steps: int = 10
    created_at: str = ""
    completed_at: str | None = None
    steps: list[AgentStepEvent] = []
