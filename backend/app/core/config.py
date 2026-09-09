"""
Kavach AI — Application Configuration
Constants for the on-prem deployment. Override via env in deployment scripts.
"""

import os

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

    embed_model: str = "nomic-embed-text:latest"

    cors_origins: tuple[str, ...] = ("http://localhost:3000",)


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as exc:
        raise RuntimeError(f"{name} must be an integer") from exc


def load_settings() -> Settings:
    """Load documented deployment overrides once at process startup."""
    defaults = Settings()
    cors = os.getenv("KAVACH_CORS_ORIGINS")
    return Settings(
        HOST=os.getenv("KAVACH_HOST", defaults.HOST),
        PORT=_env_int("KAVACH_PORT", defaults.PORT),
        ollama_host=os.getenv("OLLAMA_HOST", defaults.ollama_host),
        db_path=os.getenv("KAVACH_DB_PATH", defaults.db_path),
        upload_dir=os.getenv("KAVACH_UPLOAD_DIR", defaults.upload_dir),
        output_dir=os.getenv("KAVACH_OUTPUT_DIR", defaults.output_dir),
        knowledge_dir=os.getenv("KAVACH_KNOWLEDGE_DIR", defaults.knowledge_dir),
        cors_origins=(
            tuple(origin.strip() for origin in cors.split(",") if origin.strip())
            if cors
            else defaults.cors_origins
        ),
    )


settings = load_settings()
