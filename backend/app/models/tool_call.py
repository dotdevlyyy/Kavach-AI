"""
Kavach AI — ToolCall Model
Represents a single tool invocation by the agent.
"""

import uuid
from tortoise import fields, models
from app.schemas.common import ToolCallStatus


class ToolCall(models.Model):
    """A tool call made during message generation or agent execution."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    message = fields.ForeignKeyField(
        "models.Message", related_name="tool_calls", on_delete=fields.SET_NULL, null=True
    )
    agent_task = fields.ForeignKeyField(
        "models.AgentTask",
        related_name="tool_calls",
        on_delete=fields.SET_NULL,
        null=True,
    )
    tool_name = fields.CharField(max_length=100)
    tool_input = fields.JSONField(default=dict)
    tool_output = fields.TextField(default="")
    status = fields.CharEnumField(
        enum_type=ToolCallStatus, max_length=20, default=ToolCallStatus.PENDING
    )
    duration_ms = fields.IntField(default=0)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "tool_calls"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"ToolCall({self.id}, {self.tool_name}, {self.status})"
