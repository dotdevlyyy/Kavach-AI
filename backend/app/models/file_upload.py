"""
Kavach AI — FileUpload Model
Represents a file uploaded to a conversation.
"""

import uuid

from tortoise import fields, models


class FileUpload(models.Model):
    """A file uploaded by a user, optionally associated with a conversation."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    conversation = fields.ForeignKeyField(
        "models.Conversation",
        related_name="file_uploads",
        on_delete=fields.SET_NULL,
        null=True,
    )
    original_name = fields.CharField(max_length=500)
    stored_path = fields.CharField(max_length=1000)
    file_type = fields.CharField(max_length=50)
    file_size = fields.IntField()
    mime_type = fields.CharField(max_length=200, default="application/octet-stream")
    uploaded_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "file_uploads"
        ordering = ["-uploaded_at"]

    def __str__(self) -> str:
        return f"FileUpload({self.id}, {self.original_name})"
