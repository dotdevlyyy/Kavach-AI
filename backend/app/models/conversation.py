"""
Kavach AI — Conversation Model
Represents a chat conversation (multi-turn or agent mode).
"""

import uuid

from tortoise import fields, models


class Conversation(models.Model):
    """A chat conversation containing multiple messages."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    title = fields.CharField(max_length=500, default="New Conversation")
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    is_agent_mode = fields.BooleanField(default=False)
    metadata = fields.JSONField(default=dict)
    model_override = fields.CharField(max_length=100, null=True)
    system_prompt = fields.TextField(null=True)

    # Reverse relations
    messages: fields.ReverseRelation["app.models.message.Message"]  # noqa: F821
    agent_tasks: fields.ReverseRelation["app.models.agent_task.AgentTask"]  # noqa: F821

    class Meta:
        table = "conversations"
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return f"Conversation({self.id}, {self.title})"
