"""
Kavach AI — msgspec JSON Response Adapter for FastAPI
Provides 10-50x faster JSON serialization than the default JSONResponse.
"""

import msgspec
from starlette.responses import Response


class MsgspecJSONResponse(Response):
    """Custom FastAPI response that uses msgspec for JSON encoding.

    This replaces the default JSONResponse to leverage msgspec's C-extension
    encoder which is 10-50x faster than stdlib json and significantly faster
    than Pydantic's serialization.
    """

    media_type = "application/json"

    def __init__(
        self,
        content,
        status_code: int = 200,
        headers: dict[str, str] | None = None,
        **kwargs,
    ):
        # msgspec.json.encode returns bytes directly — no intermediate string
        body = msgspec.json.encode(content)
        super().__init__(
            content=body,
            status_code=status_code,
            headers=headers,
            media_type=self.media_type,
        )


def decode_request(body: bytes, schema_type: type):
    """Decode a request body into a msgspec Struct.

    Args:
        body: Raw request body bytes
        schema_type: The msgspec.Struct class to decode into

    Returns:
        Decoded struct instance

    Raises:
        msgspec.ValidationError: If body doesn't match schema
    """
    return msgspec.json.decode(body, type=schema_type)
