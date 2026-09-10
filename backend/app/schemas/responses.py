"""OpenAPI response contracts for stable frontend endpoints."""

from typing import Any

from pydantic import BaseModel


class FileMetadataResponse(BaseModel):
    id: str
    original_name: str
    file_type: str
    file_size: int
    mime_type: str


class FileListResponse(BaseModel):
    files: list[FileMetadataResponse]


class KnowledgeIndexResponse(BaseModel):
    document_id: str
    filename: str
    chunks_created: int
    chunks_requested: int


class KnowledgeHitResponse(BaseModel):
    chunk_id: str
    document_id: str
    document_name: str
    content: str
    score: float
    source: str
    metadata: dict[str, Any]


class KnowledgeSearchResponse(BaseModel):
    query: str
    search_type: str
    results: list[KnowledgeHitResponse]
    count: int


class KnowledgeDocumentResponse(BaseModel):
    id: str
    filename: str
    original_name: str
    file_type: str
    file_size: int
    is_knowledge_base: bool
    chunk_count: int
    created_at: str


class KnowledgeDocumentsResponse(BaseModel):
    documents: list[KnowledgeDocumentResponse]
    total: int


class ModelResponse(BaseModel):
    name: str
    purpose: str
    task_types: list[str]
    size_gb: float
    is_loaded: bool
    installed: bool
    loaded: bool
    ready: bool
    parameters: str
    quantization: str


class ModelsResponse(BaseModel):
    models: list[ModelResponse]
    count: int


class RunningModelResponse(BaseModel):
    name: str
    size_vram: int
    expires_at: str | None
    processor: str


class RunningModelsResponse(BaseModel):
    running: list[RunningModelResponse]
    count: int


class HealthModelResponse(BaseModel):
    name: str
    kind: str
    installed: bool | None
    loaded: bool | None
    ready: bool


class HealthResponse(BaseModel):
    status: str
    app: str
    version: str
    air_gapped: bool | None
    uptime_seconds: int
    disk_usage_gb: float
    ollama: dict[str, Any]
    database: dict[str, Any]
    network_monitor: dict[str, Any]
    models: dict[str, HealthModelResponse]


class ActionResponse(BaseModel):
    status: str
    conversation_id: str | None = None
    task_id: str | None = None
    document_id: str | None = None
    chunks_removed: int | None = None


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    model_used: str | None
    task_type: str | None
    words_in: int
    words_out: int
    latency_ms: int
    files: list[str]
    created_at: str


class ConversationSummaryResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class ConversationsResponse(BaseModel):
    conversations: list[ConversationSummaryResponse]
    total: int


class ConversationResponse(ConversationSummaryResponse):
    model_override: str | None
    system_prompt: str | None
    messages: list[MessageResponse]


class TaskSummaryResponse(BaseModel):
    id: str
    description: str
    status: str
    total_steps: int
    created_at: str


class TasksResponse(BaseModel):
    tasks: list[TaskSummaryResponse]
    total: int


class AgentStepResponse(BaseModel):
    step_number: int
    type: str
    content: str
    created_at: str


class TaskResponse(BaseModel):
    task_id: str
    description: str
    status: str
    total_steps: int
    created_at: str
    steps: list[AgentStepResponse]


class PreviewResponse(BaseModel):
    id: str
    file_type: str
    preview_kind: str
    text: str | None = None
    truncated: bool | None = None
    image_url: str | None = None
    download_url: str | None = None


class NetworkConnectionResponse(BaseModel):
    process: str
    protocol: str
    local_address: str
    remote_address: str
    status: str
    is_local: bool


class NetworkResponse(BaseModel):
    total_connections: int
    local_count: int
    external_count: int
    local_connections_count: int
    external_connections: int
    is_air_gapped: bool | None
    air_gap_status: str
    monitor_error: str | None
    timestamp: str | None
    persisted_rows: int
    connections: list[NetworkConnectionResponse]


class NetworkLogResponse(BaseModel):
    id: int
    timestamp: str
    local_addr: str
    remote_addr: str
    protocol: str
    status: str
    process_name: str | None
    is_local: bool


class NetworkLogsResponse(BaseModel):
    logs: list[NetworkLogResponse]
    total: int
