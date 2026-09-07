"""
Kavach AI — File Upload/Download Schemas
msgspec Structs for the /api/files endpoints.
"""

import msgspec


class UploadedFile(msgspec.Struct):
    """Metadata for a single uploaded file."""
    id: str
    original_name: str
    file_type: str  # "pdf", "image", "docx", "xlsx", "txt", "csv"
    file_size: int  # Bytes
    mime_type: str


class FileUploadResponse(msgspec.Struct):
    """Response for POST /api/files/upload."""
    files: list[UploadedFile]


class ModelInfo(msgspec.Struct):
    """Information about an available model."""
    name: str
    purpose: str
    task_types: list[str]
    size_gb: float
    is_loaded: bool
    parameters: str
    quantization: str = "Q4_K_M"


class ModelsResponse(msgspec.Struct):
    """Response for GET /api/models."""
    models: list[ModelInfo]


class RunningModel(msgspec.Struct):
    """A model currently loaded in memory."""
    name: str
    size_vram: int  # Bytes of VRAM used
    expires_at: str | None = None  # Null if keep_alive=-1
    processor: str = "gpu"


class ModelPsResponse(msgspec.Struct):
    """Response for GET /api/models/ps."""
    running: list[RunningModel]


class HealthResponse(msgspec.Struct):
    """Response for GET /api/health."""
    status: str  # "healthy" | "degraded" | "unhealthy"
    ollama: dict
    database: dict
    models: dict[str, bool]
    disk_usage_gb: float = 0.0
    uptime_seconds: int = 0
    version: str = "1.0.0"


class NetworkConnection(msgspec.Struct):
    """A single network connection."""
    local_address: str
    remote_address: str
    protocol: str
    status: str
    process: str | None = None
    is_local: bool = True


class NetworkConnectionsResponse(msgspec.Struct):
    """Response for GET /api/network/connections."""
    connections: list[NetworkConnection]
    total_connections: int
    external_connections: int  # Should always be 0
    is_air_gapped: bool = True
    timestamp: str = ""
