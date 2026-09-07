"""
Kavach AI — Task Classifier
Heuristic keyword + attachment-based classifier that determines the task type
for automatic model routing. Uses keyword scoring (not an LLM classifier) for
zero-latency classification.
"""

from __future__ import annotations

import re

from app.schemas.common import TaskType, RoutingMetadata


# ─── Keyword Sets ─────────────────────────────────────────────────────────

CODE_KEYWORDS: set[str] = {
    "code", "function", "class", "debug", "error", "bug", "script",
    "python", "javascript", "typescript", "java", "sql", "html", "css",
    "api", "endpoint", "database", "query", "algorithm", "regex",
    "compile", "syntax", "variable", "loop", "array", "dict",
    "import", "install", "pip", "npm", "git", "docker",
    "refactor", "optimize", "test", "unittest", "pytest",
    "def ", "class ", "return ", "if __name__",
    "```python", "```js", "```sql", "```bash",
}

VISION_KEYWORDS: set[str] = {
    "image", "photo", "picture", "drawing", "diagram", "scan",
    "scanned", "p&id", "pid", "isometric", "blueprint", "sketch",
    "handwritten", "photograph", "screenshot", "chart", "graph",
    "what do you see", "describe this", "read this", "extract from",
    "ocr", "recognize", "identify in",
}

DOCUMENT_KEYWORDS: set[str] = {
    "draft", "write a", "compose", "prepare", "create a note",
    "approval note", "memo", "letter", "report", "presentation",
    "word doc", "docx", "excel", "xlsx", "pptx", "powerpoint",
    "template", "format", "generate document",
}

SUMMARIZE_KEYWORDS: set[str] = {
    "summarize", "summary", "key points", "main findings",
    "brief", "overview", "tldr", "highlights", "gist",
    "condense", "distill",
}

# Image file extensions for attachment-based classification
IMAGE_EXTENSIONS: set[str] = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".tiff", ".svg"}
PDF_EXTENSION: str = ".pdf"


def classify_task(
    message: str,
    has_images: bool = False,
    has_pdfs: bool = False,
    file_types: list[str] | None = None,
) -> tuple[TaskType, float, str]:
    """Classify user message into a task type for model routing.

    Uses a priority-based heuristic:
    1. Attachment type overrides (images → VISION, scanned PDFs → OCR)
    2. Keyword scoring across categories
    3. Code block detection via regex
    4. Default fallback to GENERAL_CHAT

    Args:
        message: The user's message text
        has_images: Whether image files are attached
        has_pdfs: Whether PDF files are attached
        file_types: List of file extension strings (e.g., [".pdf", ".png"])

    Returns:
        Tuple of (TaskType, confidence_score, reasoning_string)
    """
    message_lower = message.lower().strip()
    file_types = file_types or []
    reasons: list[str] = []

    # ── Rule 1: Image attachments → Vision ─────────────────────────────
    if has_images or any(ft.lower() in IMAGE_EXTENSIONS for ft in file_types):
        reasons.append("Image file(s) attached")
        return TaskType.VISION, 0.95, "; ".join(reasons)

    # ── Rule 2: Scanned PDF + relevant keywords → OCR ──────────────────
    if has_pdfs or any(ft.lower() == PDF_EXTENSION for ft in file_types):
        ocr_hints = {"read", "extract", "scan", "ocr", "what", "text from"}
        if any(kw in message_lower for kw in ocr_hints):
            reasons.append("PDF attached with OCR-related keywords")
            return TaskType.OCR, 0.90, "; ".join(reasons)

    # ── Rule 3: Keyword scoring ────────────────────────────────────────
    code_score = sum(1 for kw in CODE_KEYWORDS if kw in message_lower)
    vision_score = sum(1 for kw in VISION_KEYWORDS if kw in message_lower)
    doc_score = sum(1 for kw in DOCUMENT_KEYWORDS if kw in message_lower)
    summarize_score = sum(1 for kw in SUMMARIZE_KEYWORDS if kw in message_lower)

    # ── Rule 4: Code block detection boost ─────────────────────────────
    if "```" in message or re.search(r"def\s+\w+|class\s+\w+|import\s+\w+", message):
        code_score += 5
        reasons.append("Code block or code patterns detected")

    # ── Rule 5: Highest score wins ─────────────────────────────────────
    scores = {
        TaskType.CODE_GENERATION: code_score,
        TaskType.VISION: vision_score,
        TaskType.DOCUMENT_DRAFT: doc_score,
        TaskType.SUMMARIZATION: summarize_score,
    }

    max_type = max(scores, key=lambda k: scores[k])
    max_score = scores[max_type]

    if max_score >= 2:
        # Find matched keywords for reasoning
        if max_type == TaskType.CODE_GENERATION:
            matched = [kw for kw in CODE_KEYWORDS if kw in message_lower]
        elif max_type == TaskType.VISION:
            matched = [kw for kw in VISION_KEYWORDS if kw in message_lower]
        elif max_type == TaskType.DOCUMENT_DRAFT:
            matched = [kw for kw in DOCUMENT_KEYWORDS if kw in message_lower]
        else:
            matched = [kw for kw in SUMMARIZE_KEYWORDS if kw in message_lower]

        # Normalize confidence: score / (score + 2) gives diminishing returns curve
        confidence = min(max_score / (max_score + 2), 0.95)
        reasons.append(f"Detected {max_type.value} keywords: {matched[:5]}")
        return max_type, confidence, "; ".join(reasons)

    # ── Default: General chat ──────────────────────────────────────────
    reasons.append("No strong keyword signals; defaulting to general chat")
    return TaskType.GENERAL_CHAT, 0.5, "; ".join(reasons)


def build_routing_metadata(
    task_type: TaskType,
    model_selected: str,
    confidence: float,
    reasoning: str,
) -> RoutingMetadata:
    """Build a RoutingMetadata struct for inclusion in SSE metadata events."""
    return RoutingMetadata(
        task_type=task_type.value,
        model_selected=model_selected,
        confidence=round(confidence, 2),
        reasoning=reasoning,
    )
