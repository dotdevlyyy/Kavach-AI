"""
Kavach AI — Database Configuration
Tortoise ORM with SQLite + WAL mode + FTS5 full-text search.
"""

from loguru import logger
from app.core.config import settings
from app.core.paths import DATA_ROOT  # noqa: F401 — imported for mkdir side-effect

TORTOISE_ORM = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": settings.db_path,
            },
        }
    },
    "apps": {
        "models": {
            "models": [
                "app.models.conversation",
                "app.models.message",
                "app.models.tool_call",
                "app.models.agent_task",
                "app.models.agent_step",
                "app.models.document",
                "app.models.knowledge_chunk",
                "app.models.file_upload",
                "app.models.network_log",
            ],
            "default_connection": "default",
        },
    },
}


async def init_sqlite_pragmas():
    """Set SQLite WAL mode and other performance pragmas after Tortoise init."""
    from tortoise import Tortoise

    conn = Tortoise.get_connection("default")
    await conn.execute_query("PRAGMA journal_mode=WAL;")
    await conn.execute_query("PRAGMA synchronous=NORMAL;")
    await conn.execute_query("PRAGMA cache_size=-64000;")  # 64MB cache
    await conn.execute_query("PRAGMA foreign_keys=ON;")
    logger.info("✅ SQLite WAL mode and performance pragmas set")


async def init_fts5():
    """Create the FTS5 virtual table. Index rows are populated explicitly by
    pipeline.ingest_document and api/knowledge.delete_document so we don't depend
    on triggers coupling schema to Python."""
    from tortoise import Tortoise

    conn = Tortoise.get_connection("default")

    await conn.execute_query("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            chunk_id,
            content,
            document_name,
            tokenize='porter unicode61'
        );
    """)

    logger.info("✅ FTS5 virtual table created (populated explicitly by pipeline)")

async def init_db():
    from tortoise import Tortoise
    # ponytail: kept for sync TestClient fixtures (tests/test_integration.py).
    # Drop once tests move to httpx.AsyncClient — silent typo-swallowing is otherwise risky.
    await Tortoise.init(config=TORTOISE_ORM, _enable_global_fallback=True)
    await Tortoise.generate_schemas()
    await init_sqlite_pragmas()
    await init_fts5()
    logger.info("✅ Database initialized")

async def close_db():
    from tortoise import Tortoise
    await Tortoise.close_connections()
    logger.info("Database connections closed")
