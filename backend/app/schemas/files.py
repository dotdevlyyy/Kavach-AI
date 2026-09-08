"""
Kavach AI — File Upload/Download Schemas
msgspec Structs for the /api/files endpoints.
"""

import msgspec


class UploadedFile(msgspec.Struct):
    """Metadata for a single uploaded file."""
    id: str
    original_name: str
    file_type: str
    file_size: int
    mime_type: str


class FileUploadResponse(msgspec.Struct):
    """Response for POST /api/files/upload."""
    files: list[UploadedFile]
