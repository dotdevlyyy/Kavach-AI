import base64
from pathlib import Path

from app.core.ollama_client import ollama_client
from app.core.paths import UPLOAD_DIR, resolve_data_path, resolve_within
from app.tools.registry import register_tool


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


@register_tool("analyze_engineering_diagram")
async def analyze_engineering_diagram(
    filepath: str = "", query: str = "", file_id: str = ""
) -> str:
    """Analyze P&ID diagrams or engineering drawings and answer questions about them.

    Args:
        filepath: Path to the image file, relative to backend/data/
        file_id: UUID of an uploaded FileUpload row (preferred over filepath)
        query: Specific question about the diagram, such as valve tag numbers.
    """
    target = await _resolve_path(file_id or None, filepath or None)
    if not target or not target.exists() or not target.is_file():
        return f"Error: Image {file_id or filepath} not found."

    try:
        with open(target, "rb") as f:
            b64_image = base64.b64encode(f.read()).decode("utf-8")

        response = await ollama_client.chat(
            model="qwen2.5vl:3b",
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Analyze this engineering diagram carefully and answer this query: {query}"
                    ),
                    "images": [b64_image],
                }
            ],
            keep_alive=-1,
        )
        return response.message.content
    except Exception:
        return "Error analyzing diagram."
