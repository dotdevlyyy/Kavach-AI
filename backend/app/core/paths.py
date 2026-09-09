"""
Kavach AI — Filesystem Path Constants
Single source of truth for upload/output/data directories.
"""

from pathlib import Path

from app.core.config import settings

DATA_ROOT = Path(settings.db_path).resolve().parent
UPLOAD_DIR = Path(settings.upload_dir).resolve()
OUTPUT_DIR = Path(settings.output_dir).resolve()
KNOWLEDGE_DIR = Path(settings.knowledge_dir).resolve()

for _d in (DATA_ROOT, UPLOAD_DIR, OUTPUT_DIR, KNOWLEDGE_DIR):
    _d.mkdir(parents=True, exist_ok=True)


def resolve_within(root: Path, path: str | Path) -> Path:
    """Resolve a path and reject traversal outside its owning directory."""
    candidate = (root / path).resolve()
    if not candidate.is_relative_to(root):
        raise ValueError("Path escapes the allowed data directory")
    return candidate


def resolve_data_path(path: str | Path) -> Path:
    return resolve_within(DATA_ROOT, path)
