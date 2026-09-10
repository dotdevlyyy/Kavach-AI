from app.core.paths import resolve_agent_workspace_path
from app.tools.registry import register_tool

MAX_FILE_BYTES = 1024 * 1024


@register_tool("file_write")
def file_write(file_path: str, content: str) -> str:
    """Write content to a file in the data directory.

    Args:
        file_path: Path relative to backend/data/workspace/
        content: The text content to write to the file
    """
    try:
        target = resolve_agent_workspace_path(file_path)
    except ValueError:
        return "Error: Access denied. Cannot write outside of data directory."

    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        return "Error: Content exceeds 1 MB write limit."
    if target.exists():
        return "Error: Refusing to overwrite an existing file."

    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
