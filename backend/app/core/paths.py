"""
Kavach AI — Filesystem Path Constants
Single source of truth for upload/output/data directories.
"""

from pathlib import Path

from app.core.config import settings

DATA_ROOT = Path(settings.db_path).resolve().parent
UPLOAD_DIR = (DATA_ROOT / "uploads").resolve()
OUTPUT_DIR = (DATA_ROOT / "outputs").resolve()

for _d in (DATA_ROOT, UPLOAD_DIR, OUTPUT_DIR):
    _d.mkdir(parents=True, exist_ok=True)
