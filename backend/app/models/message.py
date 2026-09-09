"""
Kavach AI — Message Model
Represents a single message within a conversation.
"""

import uuid

from tortoise import fields, models


class Message(models.Model):
    """A single message in a conversation (user, assistant, system, or tool)."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation", related_name="messages", on_delete=fields.CASCADE
    )
    role = fields.CharField(max_length=20)
    content = fields.TextField()
    model_used = fields.CharField(max_length=100, null=True)
    task_type = fields.CharField(max_length=50, null=True)
    tokens_in = fields.IntField(default=0)  # ponytail: word count, not tokens (V3-3)
    tokens_out = fields.IntField(default=0)  # ponytail: word count, not tokens (V3-3)
    latency_ms = fields.IntField(default=0)
    files = fields.JSONField(default=list)
    created_at = fields.DatetimeField(auto_now_add=True)

    # Reverse relations
    tool_calls: fields.ReverseRelation["app.models.tool_call.ToolCall"]  # noqa: F821

    class Meta:
        table = "messages"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"Message({self.id}, {self.role})"
