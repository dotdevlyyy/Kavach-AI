"""
Kavach AI — Common Enums and Shared Schemas
All enums used across the application and shared msgspec Structs.
"""

import enum
import msgspec


# ─── Enums ────────────────────────────────────────────────────────────────


class MessageRole(str, enum.Enum):
    """Role of a message in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class TaskType(str, enum.Enum):
    """Types of tasks the model router can classify."""
    GENERAL_CHAT = "general_chat"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    CODE_DEBUG = "code_debug"
    VISION = "vision"
    OCR = "ocr"
    DOCUMENT_ANALYSIS = "document_analysis"
    SUMMARIZATION = "summarization"
    DOCUMENT_DRAFT = "document_draft"
    SPREADSHEET = "spreadsheet"
    UNKNOWN = "unknown"


class ToolCallStatus(str, enum.Enum):
    """Status of a tool call execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"


class AgentTaskStatus(str, enum.Enum):
    """Status of an agent task."""
    PLANNING = "planning"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepType(str, enum.Enum):
    """Types of agent steps in the ReAct loop."""
    PLAN = "plan"
    ACT = "act"
    OBSERVE = "observe"
    REFLECT = "reflect"


# ─── Shared Schemas ───────────────────────────────────────────────────────


class RoutingMetadata(msgspec.Struct):
    """Metadata about model routing decision, sent to frontend."""
    task_type: str
    model_selected: str
    confidence: float
    reasoning: str


class ErrorResponse(msgspec.Struct):
    """Standard error response."""
    error: str
    detail: str | None = None
    status_code: int = 500
    request_id: str | None = None


class ServiceStatus(msgspec.Struct):
    """Status of an individual service (Ollama, DB, etc.)."""
    status: str  # "up" | "down"
    latency_ms: int
    details: str | None = None
