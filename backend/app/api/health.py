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

    db_status = "not_initialized"
    try:
        from tortoise import Tortoise

        if Tortoise.is_inited():
            conn = Tortoise.get_connection("default")
            await conn.execute_query("SELECT 1;")
            db_status = "connected"
    except Exception as e:
        logger.exception(f"Database health query failed: {e}")
        db_status = "error"

    db_ok = db_status == "connected"
    is_healthy = ollama_ok and db_ok
    is_degraded = db_ok and not ollama_ok

    # Disk usage for the data directory
    try:
        usage = shutil.disk_usage(settings.db_path)
        disk_gb = round(usage.used / (1024**3), 2)
    except OSError:
        disk_gb = 0.0

    from app.api.network import get_network_summary

    network = get_network_summary(refresh=True)
    return {
        "status": "healthy" if is_healthy else ("degraded" if is_degraded else "unhealthy"),
        "app": settings.APP_NAME,
        "version": settings.app_version,
        "air_gapped": network["is_air_gapped"],
        "uptime_seconds": int(time.monotonic() - _START_TIME),
        "disk_usage_gb": disk_gb,
        "ollama": {
            "status": "connected" if ollama_ok else "unreachable",
            "host": settings.ollama_host,
            "latency_ms": latency,
        },
        "database": {
            "status": db_status,
            "path": settings.db_path,
        },
        "network_monitor": {
            "status": network["status"],
            "timestamp": network["timestamp"],
        },
        "models": models_loaded,
    }
