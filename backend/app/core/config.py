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
    app_version: str = "1.0.0"


def load_settings() -> Settings:
    """Load settings from environment variables, falling back to defaults."""
    return Settings(
        ollama_host=os.getenv("OLLAMA_HOST", Settings.ollama_host),
        db_path=os.getenv("KAVACH_DB_PATH", Settings.db_path),
        upload_dir=os.getenv("KAVACH_UPLOAD_DIR", Settings.upload_dir),
        output_dir=os.getenv("KAVACH_OUTPUT_DIR", Settings.output_dir),
        knowledge_dir=os.getenv("KAVACH_KNOWLEDGE_DIR", Settings.knowledge_dir),
        max_agent_steps=int(os.getenv("KAVACH_MAX_AGENT_STEPS", str(Settings.max_agent_steps))),
        code_timeout_seconds=int(
            os.getenv("KAVACH_CODE_TIMEOUT", str(Settings.code_timeout_seconds))
        ),
    )


# Singleton instance
settings = load_settings()
