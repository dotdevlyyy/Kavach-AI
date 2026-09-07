"""
Kavach AI — AgentTask Model
Represents a multi-step agentic task execution.
"""

import uuid
from tortoise import fields, models
from app.schemas.common import AgentTaskStatus


class AgentTask(models.Model):
    """An autonomous agent task with multiple steps."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation", related_name="agent_tasks", on_delete=fields.CASCADE
    )
    description = fields.TextField()
    status = fields.CharEnumField(
        enum_type=AgentTaskStatus, max_length=20, default=AgentTaskStatus.PLANNING
    )
    plan = fields.JSONField(default=list)
    result_summary = fields.TextField(null=True)
    output_files = fields.JSONField(default=list)
    total_steps = fields.IntField(default=0)
    max_steps = fields.IntField(default=10)
    created_at = fields.DatetimeField(auto_now_add=True)
    completed_at = fields.DatetimeField(null=True)

    # Reverse relations
    steps: fields.ReverseRelation["app.models.agent_step.AgentStep"]

    class Meta:
        table = "agent_tasks"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"AgentTask({self.id}, {self.status})"
