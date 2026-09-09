"""
Kavach AI — AgentStep Model
Represents a single step in a ReAct agent execution.
"""

import uuid
from tortoise import fields, models
from app.schemas.common import StepType


class AgentStep(models.Model):
    """A single step in an agent task execution (Plan/Act/Observe/Reflect)."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    agent_task = fields.ForeignKeyField(
        "models.AgentTask", related_name="steps", on_delete=fields.CASCADE
    )
    step_number = fields.IntField()
    type = fields.CharEnumField(enum_type=StepType, max_length=20)
    content = fields.TextField()
    model_used = fields.CharField(max_length=100, null=True)
    tool_calls = fields.JSONField(default=list)
    duration_ms = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "agent_steps"
        ordering = ["step_number"]

    def __str__(self) -> str:
        return f"AgentStep({self.id}, step={self.step_number}, type={self.type})"
