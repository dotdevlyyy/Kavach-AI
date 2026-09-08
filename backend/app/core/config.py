"""
Kavach AI — Application Configuration
Constants for the on-prem deployment. Override via env in deployment scripts.
"""

import msgspec


class Settings(msgspec.Struct, frozen=True):
    """Application settings — single source of truth."""

    APP_NAME: str = "Kavach AI"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    app_version: str = "1.0.0"

    ollama_host: str = "http://localhost:11434"

    db_path: str = "./data/kavach.db"

    upload_dir: str = "./data/uploads"
    output_dir: str = "./data/outputs"
    knowledge_dir: str = "./data/knowledge"

    max_agent_steps: int = 10
    code_timeout_seconds: int = 30

    models: tuple[str, ...] = (
        "llama3.2:1b",
        "qwen2.5-coder:1.5b",
        "qwen2.5vl:3b",
    )

    embed_model: str = "nomic-embed-text"

    cors_origins: tuple[str, ...] = ("http://localhost:3000",)


# Singleton instance
settings = Settings()

