"""
Kavach AI — Model Registry API
Endpoints for listing available models and currently loaded (VRAM) models.
"""

from fastapi import APIRouter

from app.core.config import settings
from app.core.ollama_client import ollama_client
from app.router.router import MODEL_INFO, ROUTING_TABLE
from app.schemas.responses import ModelsResponse, RunningModelsResponse

router = APIRouter(prefix="/api/models", tags=["Models"])


@router.get("", response_model=ModelsResponse)
async def list_models():
    """
    GET /api/models
    List all models in the routing table with metadata + current load status.
    """
    inventory = await ollama_client.model_inventory()
    states = {model["name"]: model for model in inventory}

    models = []
    seen = set()
    for task_type, model_name in ROUTING_TABLE.items():
        if model_name in seen:
            continue
        seen.add(model_name)
        info = MODEL_INFO.get(model_name, {})
        models.append(
            {
                "name": model_name,
                "purpose": info.get("purpose", ""),
                "task_types": info.get("task_types", []),
                "size_gb": info.get("size_gb", 0.0),
                "is_loaded": states.get(model_name, {}).get("loaded", False),
                "installed": states.get(model_name, {}).get("installed", False),
                "loaded": states.get(model_name, {}).get("loaded", False),
                "ready": states.get(model_name, {}).get("ready", False),
                "parameters": info.get("parameters", ""),
                "quantization": info.get("quantization", "Q4_K_M"),
            }
        )

    embed = states.get(settings.embed_model, {})
    models.append(
        {
            "name": settings.embed_model,
            "purpose": "Knowledge-base embeddings",
            "task_types": ["embedding"],
            "size_gb": 0.3,
            "is_loaded": embed.get("loaded", False),
            "installed": embed.get("installed", False),
            "loaded": embed.get("loaded", False),
            "ready": embed.get("ready", False),
            "parameters": "137M",
            "quantization": "F16",
        }
    )

    return {"models": models, "count": len(models)}


@router.get("/ps", response_model=RunningModelsResponse)
async def models_ps():
    """
    GET /api/models/ps
    Models currently loaded in memory (Ollama ps).
    """
    running = await ollama_client.running_models()
    return {"running": running, "count": len(running)}
