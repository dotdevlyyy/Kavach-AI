"""
Kavach AI — KnowledgeChunk Model
Represents a text chunk from a document stored in the knowledge base.
"""

import uuid

from tortoise import fields, models


class KnowledgeChunk(models.Model):
    """A text chunk from a document, with optional embedding for semantic search."""

    id = fields.UUIDField(pk=True, default=uuid.uuid4)
    document = fields.ForeignKeyField(
        "models.Document", related_name="chunks", on_delete=fields.CASCADE
    )
    chunk_index = fields.IntField()
    content = fields.TextField()
    embedding = fields.BinaryField(null=True)  # Serialized float32 array
    metadata = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "knowledge_chunks"
        ordering = ["chunk_index"]

    def __str__(self) -> str:
        return f"KnowledgeChunk({self.id}, doc={self.document_id}, idx={self.chunk_index})"
