"""
Kavach AI — File Upload/Download API
Endpoints for uploading files, retrieving metadata, and downloading.
"""

import os
import uuid
import mimetypes
from pathlib import Path
from typing import List

import msgspec.json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, Response
from loguru import logger

from app.core.paths import UPLOAD_DIR, OUTPUT_DIR
from app.models.file_upload import FileUpload
from app.schemas.files import FileUploadResponse, UploadedFile

router = APIRouter(prefix="/api/files", tags=["Files"])


def _msgspec_response(content, status_code: int = 200) -> Response:
    """Encode a msgspec Struct to bytes for a 10x-faster response."""
    return Response(
        content=msgspec.json.encode(content),
        status_code=status_code,
        media_type="application/json",
    )


def get_file_type(filename: str, mime_type: str) -> str:
    """Classify file type from filename extension or mime type."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext in ("pdf", "docx", "xlsx", "csv", "txt", "md", "json"):
        return ext
    if mime_type.startswith("image/"):
        return "image"
    if mime_type.startswith("text/"):
        return "txt"
    return "other"


def _resolve_output_path(file_id: str) -> Path | None:
    """Scan OUTPUT_DIR for an agent-generated file whose name starts with file_id."""
    for p in OUTPUT_DIR.glob(f"{file_id}_*"):
        if p.is_file():
            return p
    return None


TEXT_PREVIEW_TYPES = {"txt", "csv", "md", "json"}
TEXT_PREVIEW_BYTES = 4096


@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    conversation_id: str | None = Form(default=None),
):
    """POST /api/files/upload — Upload one or more files."""
    uploaded_files = []

    for file in files:
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        # Atomic write: stage to a temp path, rename after DB insert succeeds.
        # Otherwise a failed DB row leaves an orphan file the user can never reference.
        staged_path = UPLOAD_DIR / f".staging_{file_id}_{uuid.uuid4().hex}"

        content = await file.read()
        mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
        file_type = get_file_type(file.filename or "", mime_type)

        with open(staged_path, "wb") as f:
            f.write(content)

        try:
            db_file = await FileUpload.create(
                id=file_id,
                conversation_id=conversation_id,
                original_name=file.filename or "unnamed",
                stored_path=str(file_path),
                file_type=file_type,
                file_size=len(content),
                mime_type=mime_type,
            )
            os.rename(staged_path, file_path)
        except Exception:
            staged_path.unlink(missing_ok=True)
            raise

        uploaded_files.append(
            UploadedFile(
                id=str(db_file.id),
                original_name=db_file.original_name,
                file_type=db_file.file_type,
                file_size=db_file.file_size,
                mime_type=db_file.mime_type,
            )
        )
        logger.info(f"Saved file {file.filename} as {file_id}")

    return _msgspec_response(FileUploadResponse(files=uploaded_files))


@router.get("/download/{file_id}")
async def download_file(file_id: str):
    """GET /api/files/download/{id} — Download a file (user upload OR agent-generated doc)."""
    db_file = await FileUpload.get_or_none(id=file_id)
    if db_file and os.path.exists(db_file.stored_path):
        return FileResponse(
            path=db_file.stored_path,
            filename=db_file.original_name,
            media_type=db_file.mime_type,
        )

    # Agent-generated docs: no FileUpload row, scan OUTPUT_DIR.
    output_path = _resolve_output_path(file_id)
    if output_path:
        mime_type = "application/pdf" if output_path.suffix.lower() == ".pdf" else "application/octet-stream"
        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type=mime_type,
            content_disposition_type="inline",
        )

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/{file_id}")
async def get_file_metadata(file_id: str):
    """GET /api/files/{id} — Retrieve file metadata."""
    db_file = await FileUpload.get_or_none(id=file_id)
    if db_file:
        return _msgspec_response(
            UploadedFile(
                id=str(db_file.id),
                original_name=db_file.original_name,
                file_type=db_file.file_type,
                file_size=db_file.file_size,
                mime_type=db_file.mime_type,
            )
        )

    # Agent-generated: best-effort metadata from the output path.
    output_path = _resolve_output_path(file_id)
    if output_path:
        try:
            size = output_path.stat().st_size
        except OSError:
            size = 0
        return _msgspec_response(
            UploadedFile(
                id=file_id,
                original_name=output_path.name,
                file_type=output_path.suffix.lstrip(".").lower(),
                file_size=size,
                mime_type="application/octet-stream",
            )
        )

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/{file_id}/preview")
async def preview_file(file_id: str):
    """
    GET /api/files/{id}/preview
    Text preview (first 4 KB) for text-like files; image preview URL otherwise.
    """
    db_file = await FileUpload.get_or_none(id=file_id)
    stored_path = db_file.stored_path if db_file else None
    if not stored_path:
        output_path = _resolve_output_path(file_id)
        if not output_path:
            raise HTTPException(status_code=404, detail="File not found")
        # Generated docs aren't text-previewable; surface the download URL instead.
        return {
            "id": file_id,
            "file_type": output_path.suffix.lstrip(".").lower() or "other",
            "preview_kind": "unsupported",
            "download_url": f"/api/files/download/{file_id}",
        }

    if not os.path.exists(stored_path):
        raise HTTPException(status_code=404, detail="File content not found on disk")

    if db_file.file_type in TEXT_PREVIEW_TYPES:
        try:
            with open(stored_path, "rb") as f:
                raw = f.read(TEXT_PREVIEW_BYTES)
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("utf-8", errors="replace")
            return {
                "id": str(db_file.id),
                "file_type": db_file.file_type,
                "preview_kind": "text",
                "text": text,
                "truncated": len(raw) >= TEXT_PREVIEW_BYTES,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Preview failed: {e}")

    if db_file.file_type == "image":
        return {
            "id": str(db_file.id),
            "file_type": "image",
            "preview_kind": "image",
            "image_url": f"/api/files/download/{file_id}",
        }

    return {
        "id": str(db_file.id),
        "file_type": db_file.file_type,
        "preview_kind": "unsupported",
        "download_url": f"/api/files/download/{file_id}",
    }

