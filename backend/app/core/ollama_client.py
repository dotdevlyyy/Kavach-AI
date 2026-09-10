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

    @staticmethod
    def _has_model(name: str, available: set[str | None]) -> bool:
        return name in available or (":" not in name and f"{name}:latest" in available)

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
            if not self._has_model(model_name, available):
                logger.error(f"Required local model is missing: {model_name}")
                continue
            try:
                await asyncio.wait_for(
                    self.client.chat(
                        model=model_name,
                        messages=[{"role": "user", "content": "hi"}],
                        keep_alive=-1,
                    ),
                    timeout=60,
                )
                self._preloaded.add(model_name)
                loaded.append(model_name)
                logger.info(f"Model loaded and warm: {model_name}")
            except Exception as exc:
                logger.error(f"Failed to preload model {model_name}: {exc}")

        if not self._has_model(settings.embed_model, available):
            logger.error(f"Required local embedding model is missing: {settings.embed_model}")
        else:
            try:
                await asyncio.wait_for(
                    self.client.embed(model=settings.embed_model, input="warmup"),
                    timeout=60,
                )
            except Exception as exc:
                logger.error(f"Failed to warm embedding model {settings.embed_model}: {exc}")

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
                    "size_vram": getattr(model, "size_vram", 0) or 0,
                    "expires_at": str(model.expires_at) if model.expires_at else None,
                    "processor": self._processor(
                        getattr(model, "size", 0) or 0,
                        getattr(model, "size_vram", 0) or 0,
                    ),
                }
                for model in (ps.models or [])
            ]
        except Exception as exc:
            logger.error(f"Failed to get running models: {exc}")
            return []

    @staticmethod
    def _processor(size: int, size_vram: int) -> str:
        if size_vram <= 0:
            return "cpu"
        if size and size_vram < size:
            return "mixed"
        return "gpu"

    async def model_inventory(self, connected: bool = True) -> list[dict]:
        required = [*settings.models, settings.embed_model]
        if not connected:
            return [
                {
                    "name": name,
                    "kind": "embedding" if name == settings.embed_model else "chat",
                    "installed": None,
                    "loaded": None,
                    "ready": False,
                }
                for name in required
            ]
        try:
            listing = await asyncio.wait_for(self.client.list(), timeout=5)
            installed = {
                getattr(item, "model", None) or getattr(item, "name", None)
                for item in getattr(listing, "models", [])
            }
        except Exception:
            installed = set()
        loaded = {model["name"] for model in await self.running_models()}
        return [
            {
                "name": name,
                "kind": "embedding" if name == settings.embed_model else "chat",
                "installed": self._has_model(name, installed),
                "loaded": self._has_model(name, loaded),
                "ready": self._has_model(name, installed) and self._has_model(name, loaded),
            }
            for name in required
        ]

    async def is_healthy(self) -> tuple[bool, int]:
        start = time.monotonic()
        try:
            await asyncio.wait_for(self.client.ps(), timeout=5)
            return True, int((time.monotonic() - start) * 1000)
        except Exception:
            return False, int((time.monotonic() - start) * 1000)


ollama_client = OllamaManager()
