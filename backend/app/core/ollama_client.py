"""Async Ollama client and local model lifecycle management."""

from __future__ import annotations

import asyncio
import time
from typing import AsyncIterator

from loguru import logger
from ollama import AsyncClient

from app.core.config import settings


class OllamaManager:
    def __init__(self, host: str | None = None):
        self.host = host or settings.ollama_host
        self.client = AsyncClient(host=self.host)
        self._preloaded: set[str] = set()

    async def preload_models(self, models: list[str] | None = None) -> list[str]:
        """Verify and warm locally installed models without network pulls."""
        healthy, _ = await self.is_healthy()
        if not healthy:
            logger.warning(f"Ollama server unreachable at {self.host}; skipping model preloading")
            return []

        try:
            listing = await asyncio.wait_for(self.client.list(), timeout=10)
            available = {
                getattr(item, "model", None) or getattr(item, "name", None)
                for item in getattr(listing, "models", [])
            }
        except Exception as exc:
            logger.warning(f"Could not list local Ollama models: {exc}")
            return []

        loaded: list[str] = []
        for model_name in models or list(settings.models):
            if model_name not in available:
                logger.error(f"Required local model is missing: {model_name}")
                continue
            try:
                await asyncio.wait_for(
                    self.client.chat(
                        model=model_name,
                        messages=[{"role": "user", "content": "hi"}],
                        keep_alive=-1,
                    ),
                    timeout=300,
                )
                self._preloaded.add(model_name)
                loaded.append(model_name)
                logger.info(f"Model loaded and warm: {model_name}")
            except Exception as exc:
                logger.error(f"Failed to preload model {model_name}: {type(exc).__name__} - {exc}")

        if settings.embed_model not in available:
            logger.error(f"Required local embedding model is missing: {settings.embed_model}")
        else:
            try:
                await asyncio.wait_for(
                    self.client.embed(model=settings.embed_model, input="warmup"),
                    timeout=300,
                )
            except Exception as exc:
                logger.error(f"Failed to warm embedding model {settings.embed_model}: {type(exc).__name__} - {exc}")

        return loaded

    async def chat(
        self,
        model: str,
        messages: list[dict],
        keep_alive: int = -1,
        **kwargs,
    ) -> dict:
        return await self.client.chat(
            model=model,
            messages=messages,
            keep_alive=keep_alive,
            **kwargs,
        )

    async def chat_stream(
        self,
        model: str,
        messages: list[dict],
        keep_alive: int = -1,
        **kwargs,
    ) -> AsyncIterator[dict]:
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
        response = await self.client.embed(model=model, input=text)
        return response.embeddings[0] if response.embeddings else []

    async def embed_many(self, model: str, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self.client.embed(model=model, input=texts)
        return list(response.embeddings)

    async def running_models(self) -> list[dict]:
        try:
            ps = await asyncio.wait_for(self.client.ps(), timeout=5)
            return [
                {
                    "name": model.model,
                    "size_vram": model.size,
                    "expires_at": str(model.expires_at) if model.expires_at else None,
                    "processor": "gpu",
                }
                for model in (ps.models or [])
            ]
        except Exception as exc:
            logger.error(f"Failed to get running models: {exc}")
            return []

    async def is_healthy(self) -> tuple[bool, int]:
        start = time.monotonic()
        try:
            await asyncio.wait_for(self.client.ps(), timeout=5)
            return True, int((time.monotonic() - start) * 1000)
        except Exception:
            return False, int((time.monotonic() - start) * 1000)


ollama_client = OllamaManager()
