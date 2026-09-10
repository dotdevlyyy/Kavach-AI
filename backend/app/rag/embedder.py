"""
Kavach AI — Embedding Generator
Uses Ollama's embed API to generate vector embeddings for RAG chunks.
"""

import array
import asyncio

from loguru import logger

from app.core.config import settings
from app.core.ollama_client import ollama_client


async def generate_embedding(text: str) -> list[float]:
    """Generate vector embeddings for a chunk of text using Ollama.

    Args:
        text: The text to embed.

    Returns:
        List of floats representing the embedding vector. Empty list on error.
    """
    try:
        return await asyncio.wait_for(
            ollama_client.embed(model=settings.embed_model, text=text), timeout=60
        )
    except Exception as e:
        logger.error(f"Embedding generation error: {e}")
        return []


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate one embedding per input in a single request."""
    if not texts:
        return []
    try:
        embeddings = await asyncio.wait_for(
            ollama_client.embed_many(model=settings.embed_model, texts=texts), timeout=60
        )
        if len(embeddings) != len(texts):
            raise ValueError("Embedding count mismatch")
        return embeddings
    except Exception as e:
        logger.error(f"Batch embedding generation error: {e}")
        return [[] for _ in texts]


def serialize_embedding(embedding: list[float]) -> bytes:
    """Serialize a float32 embedding vector to bytes for DB storage."""
    return array.array("f", embedding).tobytes()


def deserialize_embedding(data: bytes) -> list[float]:
    """Deserialize bytes back to a float32 embedding vector."""
    return list(array.array("f", data))
