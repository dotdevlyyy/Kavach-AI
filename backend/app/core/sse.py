"""
Kavach AI — SSE Event Helpers
Single source of truth for Server-Sent Events formatting.
"""

import json
from typing import Any, Literal, TypedDict


class ChatDoneEvent(TypedDict):
    conversation_id: str
    message_id: str | None
    assistant_message_id: str | None
    model: str | None
    status: Literal["completed", "stopped", "failed"]
    words_in: int
    words_out: int
    truncated: bool
    error: str | None


class AgentDoneEvent(TypedDict):
    task_id: str
    status: Literal["completed", "failed", "cancelled"]
    total_steps: int
    output_files: list[str]
    truncated: bool
    error: str | None


def sse(event: str, data: Any) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
