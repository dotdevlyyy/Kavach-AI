"""
Kavach AI — Model Router
Maps classified task types to the optimal on-premise model.

Routing Table:
  General/Summary/Document → llama3.2:1b    (~0.8 GB VRAM)
  Code tasks              → qwen2.5-coder:1.5b (~1.1 GB VRAM)
  Vision/OCR              → qwen2.5vl:3b   (~2.2 GB VRAM)
  Total VRAM:                               ~4.1 GB
"""

from __future__ import annotations

from app.schemas.common import TaskType, RoutingMetadata
from app.router.classifier import classify_task, build_routing_metadata


# ─── Routing Table ────────────────────────────────────────────────────────

ROUTING_TABLE: dict[TaskType, str] = {
    # General purpose tasks → Llama 3.2 (best general reasoning at 1B)
    TaskType.GENERAL_CHAT:      "llama3.2:1b",
    TaskType.SUMMARIZATION:     "llama3.2:1b",
    TaskType.DOCUMENT_DRAFT:    "llama3.2:1b",

    # Code tasks → Qwen2.5-Coder (specialized for code generation)
    TaskType.CODE_GENERATION:   "qwen2.5-coder:1.5b",
    TaskType.CODE_REVIEW:       "qwen2.5-coder:1.5b",
    TaskType.CODE_DEBUG:        "qwen2.5-coder:1.5b",

    # Vision/OCR tasks → Qwen2.5-VL (multimodal vision-language)
    TaskType.VISION:            "qwen2.5vl:3b",
    TaskType.OCR:               "qwen2.5vl:3b",
    TaskType.DOCUMENT_ANALYSIS: "qwen2.5vl:3b",

    # Spreadsheet (uses code model to generate processing code)
    TaskType.SPREADSHEET:       "qwen2.5-coder:1.5b",

    # Unknown defaults to general
    TaskType.UNKNOWN:           "llama3.2:1b",
}

# Model metadata for the /api/models endpoint
MODEL_INFO: dict[str, dict] = {
    "llama3.2:1b": {
        "purpose": "General chat, summarization, and document drafting",
        "task_types": ["general_chat", "summarization", "document_draft"],
        "size_gb": 0.8,
        "parameters": "1B",
        "quantization": "Q4_K_M",
    },
    "qwen2.5-coder:1.5b": {
        "purpose": "Code generation, review, debugging, and spreadsheet processing",
        "task_types": ["code_generation", "code_review", "code_debug", "spreadsheet"],
        "size_gb": 1.1,
        "parameters": "1.5B",
        "quantization": "Q4_K_M",
    },
    "qwen2.5vl:3b": {
        "purpose": "Vision, OCR, image analysis, and scanned document understanding",
        "task_types": ["vision", "ocr", "document_analysis"],
        "size_gb": 2.2,
        "parameters": "3B",
        "quantization": "Q4_K_M",
    },
}


def get_model_for_task(task_type: TaskType) -> str:
    """Return the model name for a given task type.

    Args:
        task_type: The classified task type

    Returns:
        Model name string (e.g., "llama3.2:1b")
    """
    return ROUTING_TABLE.get(task_type, "llama3.2:1b")


def get_all_models() -> list[str]:
    """Return all unique model names in the routing table."""
    return list(set(ROUTING_TABLE.values()))


def route_request(
    message: str,
    has_images: bool = False,
    has_pdfs: bool = False,
    file_types: list[str] | None = None,
    model_override: str | None = None,
) -> tuple[str, RoutingMetadata]:
    """Full routing pipeline: classify → select model → return metadata.

    If model_override is provided, bypasses classification and uses the
    specified model directly (useful for power users or testing).

    Args:
        message: User message text
        has_images: Whether image files are attached
        has_pdfs: Whether PDF files are attached
        file_types: List of file extensions
        model_override: Force a specific model (bypass router)

    Returns:
        Tuple of (model_name, RoutingMetadata)
    """
    # Step 1: Classify the task
    task_type, confidence, reasoning = classify_task(
        message=message,
        has_images=has_images,
        has_pdfs=has_pdfs,
        file_types=file_types,
    )

    # Step 2: Check for override
    if model_override:
        model = model_override
        reasoning = f"User override: {model_override} (original classification: {task_type.value})"
        confidence = 1.0
    else:
        model = get_model_for_task(task_type)

    # Step 3: Build metadata
    metadata = build_routing_metadata(
        task_type=task_type,
        model_selected=model,
        confidence=confidence,
        reasoning=reasoning,
    )

    return model, metadata
