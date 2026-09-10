"""
Kavach AI — Document Model
Represents a document indexed into the knowledge base.
"""

import uuid

from tortoise import fields, models


class Document(models.Model):
    """A document uploaded and optionally indexed into the knowledge base."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    filename = fields.CharField(max_length=500)
    original_name = fields.CharField(max_length=500)
    file_path = fields.CharField(max_length=1000)
    file_type = fields.CharField(max_length=50)
    file_size = fields.IntField()
    mime_type = fields.CharField(max_length=200)
    source_upload_id = fields.UUIDField(null=True)
    is_knowledge_base = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)

    # Reverse relations
    chunks: fields.ReverseRelation["app.models.knowledge_chunk.KnowledgeChunk"]  # noqa: F821

    class Meta:
        table = "documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Document({self.id}, {self.original_name})"
