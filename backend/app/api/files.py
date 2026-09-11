"""
Kavach AI — File Upload/Download API
Endpoints for uploading files, retrieving metadata, and downloading.
"""

import mimetypes
import os
import uuid
import zipfile
from pathlib import Path
from typing import List
from uuid import UUID

import msgspec.json
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from loguru import logger

from app.core.paths import OUTPUT_DIR, UPLOAD_DIR, resolve_upload_path
from app.models.file_upload import FileUpload
from app.schemas.files import FileUploadResponse, UploadedFile
from app.schemas.responses import FileListResponse, FileMetadataResponse, PreviewResponse

router = APIRouter(prefix="/api/files", tags=["Files"])

MAX_UPLOAD_BYTES = 20 * 1024 * 1024
MAX_UPLOAD_FILES = 10
UPLOAD_CHUNK_BYTES = 1024 * 1024
MAX_ARCHIVE_MEMBERS = 10_000
MAX_ARCHIVE_EXPANDED_BYTES = 100 * 1024 * 1024
DOCUMENT_TYPES = {"pdf", "docx", "xlsx", "csv", "txt", "md", "json"}
IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "webp", "tif", "tiff"}
CODE_EXTENSIONS = {"py", "js", "ts", "tsx", "jsx", "html", "css", "cpp", "go", "rs", "java", "sh"}
ALLOWED_EXTENSIONS = DOCUMENT_TYPES | IMAGE_EXTENSIONS | CODE_EXTENSIONS


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
    if ext in DOCUMENT_TYPES:
        return ext
    if ext in IMAGE_EXTENSIONS and mime_type.startswith("image/"):
        return "image"
    if ext in CODE_EXTENSIONS:
        return "code"
    return "other"


def _resolve_output_path(file_id: UUID) -> Path | None:
    """Scan OUTPUT_DIR for an agent-generated file whose name starts with file_id."""
    for p in OUTPUT_DIR.glob(f"{str(file_id)}_*"):
        if p.is_file():
            return p
    return None


def _normalized_filename(filename: str | None) -> str:
    name = (filename or "").replace("\\", "/").rsplit("/", 1)[-1].strip()
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    if len(name) > 500:
        raise HTTPException(status_code=400, detail="Filename too long")
    return name


def _validate_upload_header(extension: str, header: bytes) -> None:
    signatures = {
        "pdf": (b"%PDF-",),
        "png": (b"\x89PNG\r\n\x1a\n",),
        "jpg": (b"\xff\xd8\xff",),
        "jpeg": (b"\xff\xd8\xff",),
        "gif": (b"GIF87a", b"GIF89a"),
        "bmp": (b"BM",),
        "webp": (b"RIFF",),
        "tif": (b"II*\x00", b"MM\x00*"),
        "tiff": (b"II*\x00", b"MM\x00*"),
        "docx": (b"PK",),
        "xlsx": (b"PK",),
    }
    expected = signatures.get(extension)
    if expected and not any(header.startswith(prefix) for prefix in expected):
        raise HTTPException(status_code=400, detail="File content does not match extension")
    if extension == "webp" and header[8:12] != b"WEBP":
        raise HTTPException(status_code=400, detail="File content does not match extension")
    if extension in ({"txt", "md", "csv", "json"} | CODE_EXTENSIONS) and b"\x00" in header:
        raise HTTPException(status_code=400, detail="Text file contains binary content")


def _validate_mime_type(extension: str, mime_type: str) -> None:
    """Reject a declared media type that contradicts the filename."""
    mime_type = mime_type.lower().split(";", 1)[0].strip()
    if mime_type == "application/octet-stream":
        return
    if extension in IMAGE_EXTENSIONS and mime_type.startswith("image/"):
        return
    allowed = {
        "pdf": {"application/pdf"},
        "docx": {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"},
        "xlsx": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
        "json": {"application/json", "text/json"},
        "csv": {"application/vnd.ms-excel"},
        "js": {"application/javascript", "application/x-javascript"},
    }
    if extension in ({"txt", "md", "csv"} | CODE_EXTENSIONS) and mime_type.startswith("text/"):
        return
    if mime_type not in allowed.get(extension, set()):
        raise HTTPException(status_code=400, detail="File content type does not match extension")


def _validate_office_archive(extension: str, path: Path) -> None:
    if extension not in {"docx", "xlsx"}:
        return
    required = "word/document.xml" if extension == "docx" else "xl/workbook.xml"
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > MAX_ARCHIVE_MEMBERS:
                raise HTTPException(status_code=400, detail="Office archive has too many members")
            if sum(member.file_size for member in members) > MAX_ARCHIVE_EXPANDED_BYTES:
                raise HTTPException(status_code=413, detail="Office archive expands beyond 100 MB")
            if required not in {member.filename for member in members}:
                raise HTTPException(status_code=400, detail="File content does not match extension")
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="File content does not match extension")


def _media_type(path: Path) -> str:
    fallbacks = {
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    return mimetypes.guess_type(path.name)[0] or fallbacks.get(
        path.suffix.lower(), "application/octet-stream"
    )


TEXT_PREVIEW_TYPES = {"txt", "csv", "md", "json"}
PREVIEWABLE_TYPES = TEXT_PREVIEW_TYPES | {"code", "docx", "xlsx", "pptx"}
TEXT_PREVIEW_BYTES = 4096


@router.post("/upload", response_model=FileListResponse)
async def upload_files(
    files: List[UploadFile] = File(...),
    conversation_id: UUID | None = Form(default=None),
):
    """POST /api/files/upload — Upload one or more files."""
    if len(files) > MAX_UPLOAD_FILES:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_UPLOAD_FILES} files per upload")

    uploaded_files = []
    committed: list[tuple[FileUpload, Path]] = []

    try:
        for file in files:
            file_id = str(uuid.uuid4())
            original_name = _normalized_filename(file.filename)
            extension = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ""
            if extension not in ALLOWED_EXTENSIONS:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            mime_type = (
                file.content_type
                or mimetypes.guess_type(original_name)[0]
                or "application/octet-stream"
            )
            _validate_mime_type(extension, mime_type)
            file_type = get_file_type(original_name, mime_type)
            if file_type == "other":
                raise HTTPException(
                    status_code=400, detail="File content type does not match extension"
                )

            safe_filename = f"{file_id}.{extension}"
            file_path = UPLOAD_DIR / safe_filename
            staged_path = UPLOAD_DIR / f".staging_{file_id}_{uuid.uuid4().hex}"

            try:
                size = 0
                header = b""
                with open(staged_path, "wb") as staged:
                    while chunk := await file.read(UPLOAD_CHUNK_BYTES):
                        size += len(chunk)
                        if size > MAX_UPLOAD_BYTES:
                            raise HTTPException(status_code=413, detail="Max file size: 20 MB")
                        if not header:
                            header = chunk[:32]
                        staged.write(chunk)
                _validate_upload_header(extension, header)
                _validate_office_archive(extension, staged_path)
                os.replace(staged_path, file_path)

                db_file = await FileUpload.create(
                    id=file_id,
                    conversation_id=str(conversation_id) if conversation_id else None,
                    original_name=original_name,
                    stored_path=str(file_path),
                    file_type=file_type,
                    file_size=size,
                    mime_type=mime_type,
                )
                committed.append((db_file, file_path))
            except Exception:
                staged_path.unlink(missing_ok=True)
                file_path.unlink(missing_ok=True)
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
            logger.info(f"Saved file {original_name} as {file_id}")
    except Exception:
        for db_file, path in committed:
            try:
                await db_file.delete()
            except Exception as exc:
                logger.error(f"Failed to roll back upload row {db_file.id}: {exc}")
            path.unlink(missing_ok=True)
        raise

    return _msgspec_response(FileUploadResponse(files=uploaded_files))


@router.get("/download/{file_id}")
async def download_file(file_id: UUID):
    """GET /api/files/download/{id} — Download a file (user upload OR agent-generated doc)."""
    db_file = await FileUpload.get_or_none(id=str(file_id))
    try:
        upload_path = resolve_upload_path(db_file.stored_path) if db_file else None
    except ValueError:
        raise HTTPException(status_code=404, detail="File not found")
    if upload_path and upload_path.is_file():
        return FileResponse(
            path=upload_path,
            filename=db_file.original_name,
            media_type=db_file.mime_type,
            content_disposition_type="inline",
        )

    # Agent-generated docs: no FileUpload row, scan OUTPUT_DIR.
    output_path = _resolve_output_path(file_id)
    if output_path:
        mime_type = _media_type(output_path)
        return FileResponse(
            path=str(output_path),
            filename=output_path.name,
            media_type=mime_type,
            content_disposition_type="inline",
        )

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/{file_id}", response_model=FileMetadataResponse)
async def get_file_metadata(file_id: UUID):
    """GET /api/files/{id} — Retrieve file metadata."""
    db_file = await FileUpload.get_or_none(id=str(file_id))
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
                id=str(file_id),
                original_name=output_path.name,
                file_type=output_path.suffix.lstrip(".").lower(),
                file_size=size,
                mime_type=_media_type(output_path),
            )
        )

    raise HTTPException(status_code=404, detail="File not found")


@router.get("/{file_id}/preview", response_model=PreviewResponse)
async def preview_file(file_id: UUID):
    """
    GET /api/files/{id}/preview
    Text preview (first 4 KB) for text-like files; image preview URL otherwise.
    """
    db_file = await FileUpload.get_or_none(id=str(file_id))
    stored_path = db_file.stored_path if db_file else None
    if stored_path:
        try:
            stored_path = resolve_upload_path(stored_path)
        except ValueError:
            raise HTTPException(status_code=404, detail="File not found")
        file_type = db_file.file_type
    else:
        output_path = _resolve_output_path(file_id)
        if not output_path:
            raise HTTPException(status_code=404, detail="File not found")
        stored_path = output_path
        file_type = output_path.suffix.lstrip(".").lower() or "other"
    if not stored_path.is_file():
        raise HTTPException(status_code=404, detail="File content not found on disk")

    if file_type in PREVIEWABLE_TYPES:
        try:
            if file_type in TEXT_PREVIEW_TYPES | {"code"}:
                with stored_path.open("rb") as f:
                    text = f.read(TEXT_PREVIEW_BYTES).decode("utf-8", errors="replace")
            elif file_type == "docx":
                from docx import Document
                text = "\n".join(paragraph.text for paragraph in Document(stored_path).paragraphs)
            elif file_type == "xlsx":
                from openpyxl import load_workbook
                workbook = load_workbook(stored_path, read_only=True, data_only=True)
                try:
                    rows = []
                    for sheet in workbook.worksheets:
                        rows.append(f"[{sheet.title}]")
                        rows.extend("\t".join("" if cell is None else str(cell) for cell in row) for row in sheet.iter_rows(values_only=True))
                    text = "\n".join(rows)
                finally:
                    workbook.close()
            else:
                from pptx import Presentation
                presentation = Presentation(stored_path)
                text = "\n\n".join("\n".join(shape.text for shape in slide.shapes if hasattr(shape, "text")) for slide in presentation.slides)
            text = text[:TEXT_PREVIEW_BYTES]
            return {
                "id": str(file_id),
                "file_type": file_type,
                "preview_kind": "text",
                "text": text,
                "truncated": len(text) >= TEXT_PREVIEW_BYTES,
            }
        except Exception as e:
            logger.exception(f"Preview failed for {file_id}: {e}")
            raise HTTPException(status_code=500, detail="Preview failed")

    if file_type == "image":
        return {
            "id": str(file_id),
            "file_type": "image",
            "preview_kind": "image",
            "image_url": f"/api/files/download/{file_id}",
        }

    return {
        "id": str(file_id),
        "file_type": file_type,
        "preview_kind": "unsupported",
        "download_url": f"/api/files/download/{file_id}",
    }
