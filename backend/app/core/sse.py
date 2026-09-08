"""
Kavach AI — SSE Event Helpers
Single source of truth for Server-Sent Events formatting.
"""

import json
from typing import Any


def sse(event: str, data: Any) -> str:
    """Format a single SSE event."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
