"""
Kavach AI — Database Configuration
Tortoise ORM with SQLite + WAL mode + FTS5 full-text search.
"""

import os
from loguru import logger
from app.core.config import settings


# Ensure data directory exists
os.makedirs(os.path.dirname(settings.db_path), exist_ok=True)

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
    """Create FTS5 virtual table for knowledge base full-text search."""
    from tortoise import Tortoise

    conn = Tortoise.get_connection("default")

    # Create FTS5 virtual table
    await conn.execute_query("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            chunk_id,
            content,
            document_name,
            tokenize='porter unicode61'
        );
    """)

    # Trigger to keep FTS5 in sync on insert
    await conn.execute_query("""
        CREATE TRIGGER IF NOT EXISTS knowledge_chunks_ai AFTER INSERT ON knowledge_chunks
        BEGIN
            INSERT INTO knowledge_fts(chunk_id, content, document_name)
            VALUES (
                NEW.id,
                NEW.content,
                (SELECT original_name FROM documents WHERE id = NEW.document_id)
            );
        END;
    """)

    # Trigger for delete sync
    await conn.execute_query("""
        CREATE TRIGGER IF NOT EXISTS knowledge_chunks_ad AFTER DELETE ON knowledge_chunks
        BEGIN
            DELETE FROM knowledge_fts WHERE chunk_id = OLD.id;
        END;
    """)

    logger.info("✅ FTS5 virtual table and sync triggers created")

async def init_db():
    from tortoise import Tortoise
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    await init_sqlite_pragmas()
    await init_fts5()
    logger.info("✅ Database initialized")

async def close_db():
    from tortoise import Tortoise
    await Tortoise.close_connections()
    logger.info("Database connections closed")
