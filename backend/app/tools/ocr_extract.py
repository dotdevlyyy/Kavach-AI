import asyncio
import base64
from pathlib import Path

import fitz

from app.core.ollama_client import ollama_client
from app.core.paths import UPLOAD_DIR, resolve_data_path, resolve_within
from app.rag.parser import parse_pdf
from app.tools.registry import register_tool

MAX_OCR_PAGES = 20
OCR_DEADLINE_SECONDS = 120


async def _resolve_path(file_id: str | None, filepath: str | None) -> Path | None:
    """Resolve a tool input (file_id or filepath) to an absolute path."""
    if file_id:
        from app.models.file_upload import FileUpload

        upload = await FileUpload.get_or_none(id=file_id)
        if upload and upload.stored_path:
            try:
                return resolve_within(UPLOAD_DIR, Path(upload.stored_path))
            except ValueError:
                return None
    if filepath:
        try:
            return resolve_data_path(filepath)
        except ValueError:
            return None
    return None


def _image_payloads(target: Path) -> list[str]:
    """Return image payloads; render PDFs page-by-page for vision OCR."""
    if target.suffix.lower() != ".pdf":
        return [base64.b64encode(target.read_bytes()).decode("utf-8")]

    payloads = []
    with fitz.open(target) as document:
        if document.page_count > MAX_OCR_PAGES:
            raise ValueError(f"PDF exceeds {MAX_OCR_PAGES}-page OCR limit")
        for page in document:
            png = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)).tobytes("png")
            payloads.append(base64.b64encode(png).decode("utf-8"))
    return payloads


@register_tool("extract_text_from_image")
async def extract_text_from_image(filepath: str = "", file_id: str = "") -> str:
    """Extract text from a scanned document or image using Qwen2.5-VL.

    Args:
        filepath: Path to the image file, relative to backend/data/
        file_id: UUID of an uploaded FileUpload row (preferred over filepath)
    """
    target = await _resolve_path(file_id or None, filepath or None)
    if not target or not target.exists() or not target.is_file():
        return f"Error: Image {file_id or filepath} not found."

    try:
        pages = []
        async with asyncio.timeout(OCR_DEADLINE_SECONDS):
            if target.suffix.lower() == ".pdf":
                text = await asyncio.to_thread(parse_pdf, str(target))
                if len(text.strip()) >= 10:
                    return text[:100_000]
            payloads = await asyncio.to_thread(_image_payloads, target)
            for page_number, image in enumerate(payloads, start=1):
                response = await ollama_client.chat(
                    model="qwen2.5vl:3b",
                    messages=[
                        {
                            "role": "user",
                            "content": (
                                "Extract all text from this image exactly as written. "
                                "Do not add commentary."
                            ),
                            "images": [image],
                        }
                    ],
                    keep_alive=-1,
                )
                pages.append(f"[Page {page_number}]\n{response.message.content[:100_000]}")
        return "\n\n".join(pages)
    except Exception:
        return "Error extracting text from image."
