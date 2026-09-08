"""
Kavach AI — Model Registry API
Endpoints for listing available models and currently loaded (VRAM) models.
"""

from fastapi import APIRouter
from loguru import logger

from app.core.ollama_client import ollama_client
from app.router.router import ROUTING_TABLE, MODEL_INFO

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("")
async def list_models():
    """
    GET /api/models
    List all models in the routing table with metadata + current load status.
    """
    loaded_names = {m["name"] for m in await ollama_client.running_models()}

    models = []
    seen = set()
    for task_type, model_name in ROUTING_TABLE.items():
        if model_name in seen:
            continue
        seen.add(model_name)
        info = MODEL_INFO.get(model_name, {})
        models.append({
            "name": model_name,
            "purpose": info.get("purpose", ""),
            "task_types": info.get("task_types", []),
            "size_gb": info.get("size_gb", 0.0),
            "is_loaded": model_name in loaded_names,
            "parameters": info.get("parameters", ""),
            "quantization": info.get("quantization", "Q4_K_M"),
        })

    return {"models": models, "count": len(models)}


@router.get("/ps")
async def models_ps():
    """
    GET /api/models/ps
    Models currently loaded in memory (Ollama ps).
    """
    running = await ollama_client.running_models()
    return {"running": running, "count": len(running)}
