from app.core.paths import resolve_data_path
from app.tools.registry import register_tool


@register_tool("file_write")
def file_write(filepath: str, content: str) -> str:
    """Write content to a file in the data directory.

    Args:
        filepath: Path to the file, relative to backend/data/
        content: The text content to write to the file
    """
    try:
        target = resolve_data_path(filepath)
    except ValueError:
        return "Error: Access denied. Cannot write outside of data directory."

    target.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {filepath}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
