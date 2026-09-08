import base64
from pathlib import Path
from app.core.paths import DATA_ROOT
from app.tools.registry import register_tool
from app.core.ollama_client import ollama_client


async def _resolve_path(file_id: str | None, filepath: str | None) -> Path | None:
    """Resolve a tool input (file_id or filepath) to an absolute path."""
    if file_id:
        from app.models.file_upload import FileUpload
        upload = await FileUpload.get_or_none(id=file_id)
        if upload and upload.stored_path:
            return Path(upload.stored_path)
    if filepath:
        return (DATA_ROOT / filepath).resolve()
    return None


@register_tool("analyze_engineering_diagram")
async def analyze_engineering_diagram(filepath: str = "", query: str = "", file_id: str = "") -> str:
    """Analyze P&ID diagrams or engineering drawings and answer questions about them.

    Args:
        filepath: Path to the image file, relative to backend/data/
        file_id: UUID of an uploaded FileUpload row (preferred over filepath)
        query: Specific question about the diagram (e.g., "What are the tag numbers for the valves?")
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
                    "content": f"Analyze this engineering diagram carefully and answer the following query: {query}",
                    "images": [b64_image]
                }
            ],
            keep_alive=-1,
        )
        return response.message.content
    except Exception as e:
        return f"Error analyzing diagram: {str(e)}"
