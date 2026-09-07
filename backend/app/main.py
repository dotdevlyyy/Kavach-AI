"""
Kavach AI — FastAPI Application Entrypoint
Mounts CORS, lifecycle hooks (Ollama pre-loading, Tortoise ORM), and API routers.
"""

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

    yield

    # Shutdown logic
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Routers
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(files_router)


@app.get("/")
async def root():
    """Health check root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.app_version,
        "status": "online",
        "air_gapped": True
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
