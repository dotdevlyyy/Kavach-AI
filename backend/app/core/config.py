"""
Kavach AI — Application Configuration
Loads settings from environment variables with sensible defaults.
"""

import os
import msgspec


class Settings(msgspec.Struct, frozen=True):
    """Application settings loaded from environment variables."""

    # Server Settings
    APP_NAME: str = "Kavach AI"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    app_version: str = "1.0.0"

    # Ollama
    ollama_host: str = "http://localhost:11434"

    # Database
    db_path: str = "./data/kavach.db"

    # File storage
    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/outputs"
    knowledge_dir: str = "./data/knowledge"

    # Agent limits
    max_agent_steps: int = 10
    agent_timeout_seconds: int = 300  # 5 minutes

    # Code execution sandbox
    code_timeout_seconds: int = 30
    code_memory_limit_mb: int = 512

    # Models to preload
    models: tuple[str, ...] = (
        "llama3.2:1b",
        "qwen2.5-coder:1.5b",
        "qwen2.5vl:3b",
    )

    # Server
    cors_origins: tuple[str, ...] = ("http://localhost:3000",)

    @property
    def app_name(self) -> str:
        return self.APP_NAME


def load_settings() -> Settings:
    """Load settings from environment variables, falling back to defaults."""
    kwargs = {}
    if "KAVACH_APP_NAME" in os.environ:
        kwargs["APP_NAME"] = os.environ["KAVACH_APP_NAME"]
    if "KAVACH_HOST" in os.environ:
        kwargs["HOST"] = os.environ["KAVACH_HOST"]
    if "KAVACH_PORT" in os.environ:
        kwargs["PORT"] = int(os.environ["KAVACH_PORT"])
    if "KAVACH_APP_VERSION" in os.environ:
        kwargs["app_version"] = os.environ["KAVACH_APP_VERSION"]
    if "OLLAMA_HOST" in os.environ:
        kwargs["ollama_host"] = os.environ["OLLAMA_HOST"]
    if "KAVACH_DB_PATH" in os.environ:
        kwargs["db_path"] = os.environ["KAVACH_DB_PATH"]
    if "KAVACH_UPLOAD_DIR" in os.environ:
        kwargs["upload_dir"] = os.environ["KAVACH_UPLOAD_DIR"]
    if "KAVACH_OUTPUT_DIR" in os.environ:
        kwargs["output_dir"] = os.environ["KAVACH_OUTPUT_DIR"]
    if "KAVACH_KNOWLEDGE_DIR" in os.environ:
        kwargs["knowledge_dir"] = os.environ["KAVACH_KNOWLEDGE_DIR"]
    if "KAVACH_MAX_AGENT_STEPS" in os.environ:
        kwargs["max_agent_steps"] = int(os.environ["KAVACH_MAX_AGENT_STEPS"])
    if "KAVACH_CODE_TIMEOUT" in os.environ:
        kwargs["code_timeout_seconds"] = int(os.environ["KAVACH_CODE_TIMEOUT"])
    if "KAVACH_CORS_ORIGINS" in os.environ:
        kwargs["cors_origins"] = tuple(os.environ["KAVACH_CORS_ORIGINS"].split(","))

    return Settings(**kwargs)


# Singleton instance
settings = load_settings()
