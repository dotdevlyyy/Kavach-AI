"""Shared validation for persisted upload references."""

from pathlib import Path

from app.core.paths import resolve_upload_path
from app.models.file_upload import FileUpload

MAX_ATTACHMENT_BYTES = 40 * 1024 * 1024
MAX_ATTACHMENT_IMAGES = 4
CHAT_ATTACHMENT_TYPES = {"txt", "md", "csv", "json", "code", "pdf", "docx", "image"}
AGENT_ATTACHMENT_TYPES = {"pdf", "image"}


class UploadLimitError(ValueError):
    pass


async def resolve_uploads(
    file_ids: list[str], allowed_types: set[str] | None = None
) -> list[tuple[FileUpload, Path]]:
    uploads = await FileUpload.filter(id__in=file_ids)
    by_id = {str(upload.id): upload for upload in uploads}
    if missing := [file_id for file_id in file_ids if file_id not in by_id]:
        raise ValueError(f"Attachment not found: {missing[0]}")

    resolved = []
    for file_id in file_ids:
        upload = by_id[file_id]
        if allowed_types is not None and upload.file_type not in allowed_types:
            raise ValueError(f"Unsupported attachment type: {upload.file_type}")
        path = resolve_upload_path(upload.stored_path)
        if not path.is_file():
            raise ValueError(f"Attachment content unavailable: {file_id}")
        resolved.append((upload, path))
    if sum(upload.file_size for upload, _ in resolved) > MAX_ATTACHMENT_BYTES:
        raise UploadLimitError("Attachments exceed 40 MB aggregate limit")
    if sum(upload.file_type == "image" for upload, _ in resolved) > MAX_ATTACHMENT_IMAGES:
        raise UploadLimitError("Maximum 4 image attachments")
    return resolved
