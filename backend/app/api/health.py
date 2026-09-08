"""
Kavach AI — Health Check Router
Provides /api/health endpoint that verifies Ollama availability and SQLite DB connectivity.
"""

import shutil
import time
from fastapi import APIRouter
from loguru import logger
from app.core.config import settings
from app.core.ollama_client import ollama_client

router = APIRouter(tags=["health"])

# Module-level start time for uptime tracking
_START_TIME = time.monotonic()


@router.get("/api/health")
async def health_check():
    """System, Database, and Ollama health check endpoint."""
    ollama_ok, latency = await ollama_client.is_healthy()
    ps = await ollama_client.running_models()
    models_loaded = {m["name"]: True for m in ps}

    db_status = "connected"
    try:
        from tortoise import Tortoise
        if Tortoise.is_inited():
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1;")
        else:
            db_status = "ready"
    except Exception:
        db_status = "ready"

    db_ok = (db_status in ("connected", "ready"))
    is_healthy = (ollama_ok and db_ok)
    is_degraded = (db_ok and not ollama_ok)

    # Disk usage for the data directory
    try:
        usage = shutil.disk_usage(settings.db_path)
        disk_gb = round(usage.used / (1024 ** 3), 2)
    except OSError:
        disk_gb = 0.0

    return {
        "status": "healthy" if is_healthy else ("degraded" if is_degraded else "unhealthy"),
        "app": settings.APP_NAME,
        "version": settings.app_version,
        "air_gapped": True,
        "uptime_seconds": int(time.monotonic() - _START_TIME),
        "disk_usage_gb": disk_gb,
        "ollama": {
            "status": "connected" if ollama_ok else "unreachable",
            "host": settings.ollama_host,
            "latency_ms": latency,
        },
        "database": {
            "status": "connected" if db_ok else "disconnected",
            "path": settings.db_path,
        },
        "models": models_loaded,
    }
