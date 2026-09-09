"""
Kavach AI — Agent Request/Response Schemas
Request models use Pydantic for FastAPI compatibility; event payloads use plain dicts.
"""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AgentExecuteRequest(BaseModel):
    """Request body for POST /api/agent/execute."""

    task_description: str = Field(max_length=20_000)
    conversation_id: UUID | None = None
    file_ids: list[UUID] = Field(default_factory=list, max_length=10)
    files: list[UUID] = Field(default_factory=list, max_length=10)
    model_override: Literal["llama3.2:1b", "qwen2.5-coder:1.5b", "qwen2.5vl:3b"] | None = None
    system_prompt: str | None = Field(default=None, max_length=10_000)
    max_steps: int = Field(default=10, ge=1, le=10)

    @field_validator("task_description")
    @classmethod
    def task_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Task description cannot be empty")
        return value
