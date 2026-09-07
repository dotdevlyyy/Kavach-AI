"""
Kavach AI — Embedding Generator
Uses Ollama's embed API to generate vector embeddings for RAG chunks.
"""

import struct
from loguru import logger
from app.core.ollama_client import ollama_client


async def generate_embedding(text: str) -> list[float]:
    """Generate vector embeddings for a chunk of text using Ollama.

    Args:
        text: The text to embed.

    Returns:
        List of floats representing the embedding vector. Empty list on error.
    """
    try:
        return await ollama_client.embed(model="llama3.2:1b", text=text)
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return []


def serialize_embedding(embedding: list[float]) -> bytes:
    """Serialize a float32 embedding vector to bytes for DB storage."""
    return struct.pack(f"{len(embedding)}f", *embedding)


def deserialize_embedding(data: bytes) -> list[float]:
    """Deserialize bytes back to a float32 embedding vector."""
    count = len(data) // 4
    return list(struct.unpack(f"{count}f", data))
