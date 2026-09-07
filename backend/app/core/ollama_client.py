"""
Kavach AI — Ollama Client & GPU Hot-Swap Manager
Async wrapper around ollama.AsyncClient with model preloading and lifecycle management.

All 3 models are preloaded at startup with keep_alive=-1 (never unloaded from VRAM),
enabling instant switching between models with zero cold-start latency.
"""

from __future__ import annotations

import asyncio
from typing import AsyncIterator

from loguru import logger
from ollama import AsyncClient

from app.core.config import settings


class OllamaManager:
    """Manages Ollama model lifecycle, preloading, and inference.

    Wraps ollama.AsyncClient to provide:
    - Model preloading with keep_alive=-1 (pin to VRAM)
    - Streaming and non-streaming chat
    - Embedding generation for RAG
    - Model status queries
    """

    def __init__(self, host: str | None = None):
        self.host = host or settings.ollama_host
        self.client = AsyncClient(host=self.host)
        self._preloaded: set[str] = set()

    async def preload_models(self, models: list[str] | None = None) -> list[str]:
        """Pull and preload models into VRAM with keep_alive=-1.

        Args:
            models: List of model names to preload. Defaults to settings.models.

        Returns:
            List of successfully preloaded model names.
        """
        models = models or list(settings.models)
        loaded: list[str] = []

        for model_name in models:
            try:
                # Attempt to pull (no-op if already available)
                logger.info(f"📦 Pulling model: {model_name}")
                try:
                    await self.client.pull(model_name)
                    logger.info(f"✅ Model pulled: {model_name}")
                except Exception as e:
                    logger.warning(f"⚠️ Pull skipped (may already exist): {model_name} — {e}")

                # Warm up: send a minimal request with keep_alive=-1
                logger.info(f"🔥 Warming up model: {model_name}")
                await self.client.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": "hi"}],
                    keep_alive=-1,  # CRITICAL: Keep in VRAM forever
                )
                self._preloaded.add(model_name)
                loaded.append(model_name)
                logger.info(f"✅ Model loaded and warm: {model_name}")

            except Exception as e:
                logger.error(f"❌ Failed to preload model {model_name}: {e}")

        # Log final status
        ps = await self.running_models()
        logger.info(f"🧠 Models in VRAM: {[m['name'] for m in ps]}")

        return loaded

    async def chat(
        self,
        model: str,
        messages: list[dict],
        keep_alive: int = -1,
        **kwargs,
    ) -> dict:
        """Send a non-streaming chat request.

        Args:
            model: Model name (e.g., "llama3.2:1b")
            messages: Conversation messages [{role, content}]
            keep_alive: Model keep-alive duration (-1 = forever)

        Returns:
            Ollama chat response dict
        """
        response = await self.client.chat(
            model=model,
            messages=messages,
            keep_alive=keep_alive,
            **kwargs,
        )
        return response

    async def chat_stream(
        self,
        model: str,
        messages: list[dict],
        keep_alive: int = -1,
        **kwargs,
    ) -> AsyncIterator[dict]:
        """Send a streaming chat request, yielding tokens.

        Args:
            model: Model name
            messages: Conversation messages
            keep_alive: Model keep-alive duration

        Yields:
            Ollama stream chunks with 'message.content' for each token
        """
        stream = await self.client.chat(
            model=model,
            messages=messages,
            stream=True,
            keep_alive=keep_alive,
            **kwargs,
        )
        async for chunk in stream:
            yield chunk

    async def embed(self, model: str, text: str) -> list[float]:
        """Generate embeddings for text using a model.

        Args:
            model: Model name (uses the default general model for embeddings)
            text: Text to embed

        Returns:
            Embedding vector as list of floats
        """
        response = await self.client.embed(model=model, input=text)
        return response.embeddings[0] if response.embeddings else []

    async def running_models(self) -> list[dict]:
        """Get list of models currently loaded in memory.

        Returns:
            List of dicts with model name, size, and processor info
        """
        try:
            ps = await self.client.ps()
            if ps.models:
                return [
                    {
                        "name": m.model,
                        "size_vram": m.size,
                        "expires_at": str(m.expires_at) if m.expires_at else None,
                        "processor": "gpu",
                    }
                    for m in ps.models
                ]
            return []
        except Exception as e:
            logger.error(f"Failed to get running models: {e}")
            return []

    async def list_models(self) -> list[dict]:
        """Get list of all available (downloaded) models.

        Returns:
            List of dicts with model metadata
        """
        try:
            response = await self.client.list()
            return [
                {
                    "name": m.model,
                    "size": m.size,
                    "modified_at": str(m.modified_at) if m.modified_at else None,
                }
                for m in response.models
            ] if response.models else []
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []

    async def is_healthy(self) -> tuple[bool, int]:
        """Check if Ollama server is reachable.

        Returns:
            Tuple of (is_healthy, latency_ms)
        """
        import time

        start = time.monotonic()
        try:
            await self.client.ps()
            latency = int((time.monotonic() - start) * 1000)
            return True, latency
        except Exception:
            latency = int((time.monotonic() - start) * 1000)
            return False, latency

    @property
    def preloaded_models(self) -> set[str]:
        """Set of model names that were successfully preloaded."""
        return self._preloaded.copy()
