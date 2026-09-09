"""
Kavach AI — Task Classifier
Heuristic keyword + attachment-based classifier that determines the task type
for automatic model routing. Uses keyword scoring (not an LLM classifier) for
zero-latency classification.
"""

from __future__ import annotations

import re

from app.schemas.common import TaskType

# ─── Keyword Sets ─────────────────────────────────────────────────────────

CODE_KEYWORDS: set[str] = {
    "code",
    "function",
    "class",
    "debug",
    "error",
    "bug",
    "script",
    "python",
    "javascript",
    "typescript",
    "java",
    "sql",
    "html",
    "css",
    "api",
    "endpoint",
    "database",
    "query",
    "algorithm",
    "regex",
    "compile",
    "syntax",
    "variable",
    "loop",
    "array",
    "dict",
    "import",
    "install",
    "pip",
    "npm",
    "git",
    "docker",
    "refactor",
    "optimize",
    "review",
    "test",
    "unittest",
    "pytest",
    "def ",
    "class ",
    "return ",
    "if __name__",
    "```python",
    "```js",
    "```sql",
    "```bash",
}

VISION_KEYWORDS: set[str] = {
    "image",
    "photo",
    "picture",
    "drawing",
    "diagram",
    "scan",
    "scanned",
    "p&id",
    "pid",
    "isometric",
    "blueprint",
    "sketch",
    "handwritten",
    "photograph",
    "screenshot",
    "chart",
    "graph",
    "what do you see",
    "describe this",
    "read this",
    "extract from",
    "ocr",
    "recognize",
    "identify in",
}

DOCUMENT_KEYWORDS: set[str] = {
    "draft",
    "write a",
    "compose",
    "prepare",
    "create a note",
    "approval note",
    "memo",
    "letter",
    "report",
    "presentation",
    "word doc",
    "docx",
    "excel",
    "xlsx",
    "pptx",
    "powerpoint",
    "template",
    "format",
    "generate document",
}

SUMMARIZE_KEYWORDS: set[str] = {
    "summarize",
    "summary",
    "key points",
    "main findings",
    "brief",
    "overview",
    "tldr",
    "highlights",
    "gist",
    "condense",
    "distill",
}

SPREADSHEET_KEYWORDS: set[str] = {"spreadsheet", "excel", "xlsx", "csv", "workbook"}
CODE_REVIEW_KEYWORDS: set[str] = {"review", "audit", "inspect"}
CODE_DEBUG_KEYWORDS: set[str] = {"debug", "bug", "error", "exception", "traceback", "fix"}

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
    normalized_types = {file_type.lower().lstrip(".") for file_type in file_types}
    reasons: list[str] = []

    # ── Rule 1: Image attachments → Vision ─────────────────────────────
    if (
        has_images
        or "image" in normalized_types
        or normalized_types & {extension.lstrip(".") for extension in IMAGE_EXTENSIONS}
    ):
        reasons.append("Image file(s) attached")
        return TaskType.VISION, 0.95, "; ".join(reasons)

    # ── Rule 2: Scanned PDF + relevant keywords → OCR ──────────────────
    if has_pdfs or "pdf" in normalized_types:
        ocr_hints = {"read", "extract", "scan", "ocr", "what", "text from"}
        if any(kw in message_lower for kw in ocr_hints):
            reasons.append("PDF attached with OCR-related keywords")
            return TaskType.OCR, 0.90, "; ".join(reasons)
        return TaskType.DOCUMENT_ANALYSIS, 0.85, "PDF document attached"

    if normalized_types & {"code", "py", "js", "ts", "tsx", "jsx", "java", "cpp", "go", "rs"}:
        return TaskType.CODE_GENERATION, 0.95, "Code file attached"

    if normalized_types & {"csv", "xlsx"}:
        return TaskType.SPREADSHEET, 0.95, "Spreadsheet attached"

    # ── Rule 3: Keyword scoring ────────────────────────────────────────
    def matches(keyword: str) -> bool:
        if keyword.strip() != keyword or any(symbol in keyword for symbol in "`_{}"):
            return keyword in message_lower
        return re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", message_lower) is not None

    code_score = sum(1 for keyword in CODE_KEYWORDS if matches(keyword))
    vision_score = sum(1 for keyword in VISION_KEYWORDS if matches(keyword))
    doc_score = sum(1 for keyword in DOCUMENT_KEYWORDS if matches(keyword))
    summarize_score = sum(1 for keyword in SUMMARIZE_KEYWORDS if matches(keyword))
    spreadsheet_score = sum(1 for keyword in SPREADSHEET_KEYWORDS if matches(keyword))

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
        TaskType.SPREADSHEET: spreadsheet_score,
    }

    max_type = max(scores, key=lambda k: scores[k])
    max_score = scores[max_type]

    if max_score >= 2:
        # Find matched keywords for reasoning
        if max_type == TaskType.CODE_GENERATION:
            matched = [keyword for keyword in CODE_KEYWORDS if matches(keyword)]
            if any(matches(keyword) for keyword in CODE_DEBUG_KEYWORDS):
                max_type = TaskType.CODE_DEBUG
            elif any(matches(keyword) for keyword in CODE_REVIEW_KEYWORDS):
                max_type = TaskType.CODE_REVIEW
        elif max_type == TaskType.VISION:
            matched = [kw for kw in VISION_KEYWORDS if kw in message_lower]
        elif max_type == TaskType.DOCUMENT_DRAFT:
            matched = [keyword for keyword in DOCUMENT_KEYWORDS if matches(keyword)]
        elif max_type == TaskType.SPREADSHEET:
            matched = [keyword for keyword in SPREADSHEET_KEYWORDS if matches(keyword)]
        else:
            matched = [keyword for keyword in SUMMARIZE_KEYWORDS if matches(keyword)]

        # Normalize confidence: score / (score + 2) gives diminishing returns curve
        confidence = min(max_score / (max_score + 2), 0.95)
        reasons.append(f"Detected {max_type.value} keywords: {matched[:5]}")
        return max_type, confidence, "; ".join(reasons)

    # ── Default: General chat ──────────────────────────────────────────
    reasons.append("No strong keyword signals; defaulting to general chat")
    return TaskType.GENERAL_CHAT, 0.5, "; ".join(reasons)
