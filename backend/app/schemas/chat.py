"""
Kavach AI — Chat Request/Response Schemas
Request models use Pydantic for FastAPI compatibility; event payloads use plain dicts.
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""
    message: str
    conversation_id: str | None = None
    file_ids: list[str] = Field(default_factory=list)
    files: list[str] = Field(default_factory=list)
    model_override: str | None = None
    system_prompt: str | None = None
    enable_knowledge_base: bool = True

