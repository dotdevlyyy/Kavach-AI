import os
import uuid
import mimetypes
from pathlib import Path
from typing import List

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from app.models.file_upload import FileUpload
from app.core.msgspec_adapter import MsgspecJSONResponse
from app.schemas.files import FileUploadResponse, UploadedFile

router = APIRouter()

UPLOAD_DIR = Path("backend/data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_DIR = Path("backend/data/outputs")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def get_file_type(filename: str, mime_type: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else ""
    if ext in ["pdf"]:
        return "pdf"
    if ext in ["doc", "docx"]:
        return "docx"
    if ext in ["xls", "xlsx"]:
        return "xlsx"
    if ext in ["csv"]:
        return "csv"
    if ext in ["txt", "md"]:
        return "txt"
    if mime_type.startswith("image/"):
        return "image"
    return "other"

@router.post("/upload", response_class=MsgspecJSONResponse)
async def upload_files(files: List[UploadFile] = File(...)):
    uploaded_files = []
    
    for file in files:
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = UPLOAD_DIR / safe_filename
        
        content = await file.read()
        mime_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
        
        with open(file_path, "wb") as f:
            f.write(content)
            
        db_file = await FileUpload.create(
            id=file_id,
            original_name=file.filename,
            saved_path=str(file_path),
            mime_type=mime_type,
            size_bytes=len(content)
        )
        
        uploaded_files.append(
            UploadedFile(
                id=str(db_file.id),
                original_name=db_file.original_name,
                file_type=get_file_type(db_file.original_name, db_file.mime_type),
                file_size=db_file.size_bytes,
                mime_type=db_file.mime_type
            )
        )
        logger.info(f"Saved file {file.filename} as {file_id}")
        
    return FileUploadResponse(files=uploaded_files)

@router.get("/{file_id}", response_class=MsgspecJSONResponse)
async def get_file_metadata(file_id: str):
    db_file = await FileUpload.get_or_none(id=file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    file_type = get_file_type(db_file.original_name, db_file.mime_type)
    return UploadedFile(
        id=str(db_file.id),
        original_name=db_file.original_name,
        file_type=file_type,
        file_size=db_file.size_bytes,
        mime_type=db_file.mime_type
    )

@router.get("/download/{file_id}")
async def download_file(file_id: str):
    db_file = await FileUpload.get_or_none(id=file_id)
    if not db_file:
        raise HTTPException(status_code=404, detail="File not found")
        
    if not os.path.exists(db_file.saved_path):
        raise HTTPException(status_code=404, detail="File content not found on disk")
        
    return FileResponse(
        path=db_file.saved_path,
        filename=db_file.original_name,
        media_type=db_file.mime_type
    )
