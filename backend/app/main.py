"""
Kavach AI — FastAPI Application Entrypoint
Mounts CORS, lifecycle hooks (Ollama pre-loading, Tortoise ORM), and API routers.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.core.config import settings
from app.core.database import init_db, close_db
from app.core.ollama_client import ollama_client

from app.api.chat import router as chat_router
from app.api.agent import router as agent_router
from app.api.files import router as files_router
from app.api.network import router as network_router
from app.api.health import router as health_router
from app.api.knowledge import router as knowledge_router
from app.api.models import router as models_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("Initializing Kavach AI Backend...")
    # Initialize Tortoise ORM + SQLite WAL mode
    await init_db()

    # Preload all 3 Ollama models into GPU memory if Ollama is available
    try:
        await ollama_client.preload_models()
    except Exception as e:
        logger.warning(f"Ollama preloading warning (server may be offline): {e}")

    # Start periodic network snapshotter so /api/network/logs shows history.
    # ponytail: 30s tick keeps DB growth bounded; tighten to 10s if demo needs finer grain.
    snapshot_task = None
    try:
        from app.api.network import _periodic_snapshotter
        snapshot_task = asyncio.create_task(_periodic_snapshotter(interval_seconds=30))
    except Exception as e:
        logger.warning(f"Network snapshotter failed to start: {e}")

    yield

    # Shutdown logic
    if snapshot_task:
        snapshot_task.cancel()
        try:
            await snapshot_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutting down Kavach AI Backend...")
    await close_db()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.app_version,
    description="Sovereign On-Premises Agentic AI Workbench for MRPL & PSUs",
    lifespan=lifespan
)

# CORS middleware for Next.js frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(files_router)
app.include_router(network_router)
app.include_router(health_router)
app.include_router(knowledge_router)
app.include_router(models_router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
