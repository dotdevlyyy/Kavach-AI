from app.core.paths import resolve_data_path
from app.tools.registry import register_tool


@register_tool("file_read")
def file_read(filepath: str) -> str:
    """Read contents of a file from the data directory.

    Args:
        filepath: Path to the file, relative to backend/data/
    """
    try:
        target = resolve_data_path(filepath)
    except ValueError:
        return "Error: Access denied. Cannot read outside of data directory."

    if not target.exists():
        return f"Error: File {filepath} not found."

    if not target.is_file():
        return f"Error: {filepath} is a directory."

    try:
        with open(target, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"
