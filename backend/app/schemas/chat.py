"""
Kavach AI — Chat Request/Response Schemas
msgspec Structs for the /api/chat endpoints.
"""

import msgspec


class ChatRequest(msgspec.Struct):
    """Request body for POST /api/chat."""
    message: str
    conversation_id: str | None = None
    file_ids: list[str] = []
    model_override: str | None = None
    system_prompt: str | None = None
    enable_knowledge_base: bool = True


class ChatMetadataEvent(msgspec.Struct):
    """SSE metadata event sent at the start of a chat response."""
    conversation_id: str
    message_id: str
    model: str
    task_type: str
    confidence: float
    reasoning: str


class ChatTokenEvent(msgspec.Struct):
    """SSE token event — a single streamed token."""
    content: str


class ChatDoneEvent(msgspec.Struct):
    """SSE done event sent when generation is complete."""
    message_id: str
    conversation_id: str
    tokens_in: int
    tokens_out: int
    latency_ms: int
    model: str


class ConversationSummary(msgspec.Struct):
    """Summary of a conversation for listing."""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    is_agent_mode: bool


class MessageResponse(msgspec.Struct):
    """A single message in a conversation."""
    id: str
    role: str
    content: str
    model_used: str | None = None
    task_type: str | None = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    files: list[str] = []
    created_at: str = ""


class ConversationDetail(msgspec.Struct):
    """Full conversation detail with messages."""
    id: str
    title: str
    created_at: str
    updated_at: str
    model_override: str | None = None
    system_prompt: str | None = None
    is_agent_mode: bool
    messages: list[MessageResponse] = []
