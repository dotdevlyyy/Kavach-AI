from app.core.paths import resolve_agent_workspace_path
from app.tools.registry import register_tool

MAX_FILE_BYTES = 1024 * 1024


@register_tool("file_read")
def file_read(file_path: str) -> str:
    """Read contents of a file from the data directory.

    Args:
        file_path: Path relative to backend/data/workspace/
    """
    try:
        target = resolve_agent_workspace_path(file_path)
    except ValueError:
        return "Error: Access denied. Cannot read outside of data directory."

    if not target.exists():
        return f"Error: File {file_path} not found."

    if not target.is_file():
        return f"Error: {file_path} is a directory."

    if target.stat().st_size > MAX_FILE_BYTES:
        return "Error: File exceeds 1 MB read limit."

    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
