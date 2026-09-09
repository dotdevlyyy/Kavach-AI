"""Streaming chat and conversation management endpoints."""

import asyncio
import base64
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from app.core.cancellation import registry as cancel_registry
from app.core.ollama_client import ollama_client
from app.core.paths import UPLOAD_DIR, resolve_within
from app.core.sse import sse
from app.models.conversation import Conversation
from app.models.message import Message
from app.rag.parser import parse_document
from app.rag.retriever import hybrid_search
from app.router.router import route_request
from app.schemas.chat import ChatRequest

router = APIRouter(prefix="/api/chat", tags=["Chat"])

DEFAULT_SYSTEM_PROMPT = (
    "You are Kavach AI, a sovereign on-premises AI workbench for Mangalore Refinery "
    "and Petrochemicals Limited (MRPL). Assist refinery engineers with technical analysis, "
    "SOPs, safety standards, inspection reports, diagrams, and report generation. "
    "Provide accurate, professional responses."
)
MAX_ATTACHMENT_TEXT_CHARS = 50_000


async def _attachment_payload(file_ids: list[str]) -> tuple[str, list[str]]:
    if not file_ids:
        return "", []

    from app.models.file_upload import FileUpload

    uploads = await FileUpload.filter(id__in=file_ids)
    text_parts: list[str] = []
    images: list[str] = []
    for upload in uploads:
        try:
            path = resolve_within(UPLOAD_DIR, Path(upload.stored_path))
        except ValueError:
            logger.error(f"Rejected stored path outside upload directory for {upload.id}")
            continue
        if not path.is_file():
            continue

        try:
            if upload.file_type in {"txt", "md", "csv", "json", "code"}:
                content = path.read_text(encoding="utf-8", errors="replace")
                text_parts.append(
                    f"--- {upload.original_name} ---\n{content[:MAX_ATTACHMENT_TEXT_CHARS]}"
                )
            elif upload.file_type in {"pdf", "docx"}:
                content = await asyncio.to_thread(parse_document, str(path))
                if len(content.strip()) < 10 and upload.file_type == "pdf":
                    from app.tools.ocr_extract import extract_text_from_image

                    content = await extract_text_from_image(file_id=str(upload.id))
                text_parts.append(
                    f"--- {upload.original_name} ---\n{content[:MAX_ATTACHMENT_TEXT_CHARS]}"
                )
            elif upload.file_type == "image":
                images.append(base64.b64encode(path.read_bytes()).decode("utf-8"))
        except Exception as exc:
            logger.exception(f"Failed to process attachment {upload.id}: {exc}")

    text = "\n\n[Attached Files]:\n" + "\n\n".join(text_parts) if text_parts else ""
    return text, images


@router.post("")
async def chat_stream_endpoint(request: ChatRequest):
    conversation_id = str(request.conversation_id or uuid.uuid4())
    file_ids = [str(file_id) for file_id in (request.file_ids or request.files)]
    conversation, created = await Conversation.get_or_create(
        id=conversation_id,
        defaults={
            "title": request.message[:80],
            "model_override": request.model_override,
            "system_prompt": request.system_prompt,
        },
    )
    model_override = request.model_override if created else conversation.model_override
    system_prompt = (
        request.system_prompt if created else conversation.system_prompt
    ) or DEFAULT_SYSTEM_PROMPT
    cancel_event = cancel_registry.get(conversation_id)

    async def event_generator():
        full_response = ""
        started = time.monotonic()
        try:
            history = list(
                reversed(
                    await Message.filter(conversation=conversation)
                    .order_by("-created_at")
                    .limit(20)
                )
            )
            user_message = await Message.create(
                conversation=conversation,
                role="user",
                content=request.message,
                files=file_ids,
            )
            selected_model, metadata = await route_request(
                message=request.message,
                file_ids=file_ids,
                model_override=model_override,
            )
            yield sse(
                "metadata",
                {
                    "conversation_id": conversation_id,
                    "message_id": str(user_message.id),
                    "model": selected_model,
                    "task_type": metadata.task_type,
                    "confidence": metadata.confidence,
                    "reasoning": metadata.reasoning,
                },
            )

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(
                {"role": message.role, "content": message.content} for message in history
            )
            attachment_text, images = await _attachment_payload(file_ids)
            user_payload = {"role": "user", "content": request.message + attachment_text}
            if images:
                user_payload["images"] = images
            messages.append(user_payload)

            if request.enable_knowledge_base:
                try:
                    hits = await hybrid_search(request.message, limit=3)
                    if hits:
                        context = "\n".join(
                            f"[{hit.get('document_name', 'KB')}] {hit['content'][:400]}"
                            for hit in hits
                        )
                        messages.insert(
                            1,
                            {
                                "role": "system",
                                "content": (
                                    f"Knowledge base context:\n{context}\n"
                                    "Cite each used source with [document_name]."
                                ),
                            },
                        )
                except Exception as exc:
                    logger.warning(f"Knowledge retrieval failed: {exc}")

            words_in = sum(len(str(message["content"]).split()) for message in messages)
            async for chunk in ollama_client.chat_stream(
                model=selected_model,
                messages=messages,
                keep_alive=-1,
                options={"temperature": 0.4},
            ):
                if cancel_event.is_set():
                    yield sse("stopped", {"conversation_id": conversation_id})
                    break
                token = (
                    chunk.message.content
                    if hasattr(chunk, "message")
                    else chunk.get("message", {}).get("content", "")
                )
                if token:
                    full_response += token
                    yield sse("token", {"content": token, "token": token})

            assistant_message = await Message.create(
                conversation=conversation,
                role="assistant",
                content=full_response,
                model_used=selected_model,
                task_type=metadata.task_type,
                tokens_in=words_in,
                tokens_out=len(full_response.split()),
                latency_ms=int((time.monotonic() - started) * 1000),
            )
            conversation.updated_at = datetime.now(timezone.utc)
            await conversation.save(update_fields=["updated_at"])
            yield sse(
                "done",
                {
                    "conversation_id": conversation_id,
                    "message_id": str(user_message.id),
                    "assistant_message_id": str(assistant_message.id),
                    "model": selected_model,
                    "status": "stopped" if cancel_event.is_set() else "completed",
                    "words_in": words_in,
                    "words_out": len(full_response.split()),
                },
            )
        except Exception as exc:
            logger.exception(f"Chat generation failed: {exc}")
            yield sse("error", {"error": "Chat generation failed"})
        finally:
            cancel_registry.clear(conversation_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/stop")
async def stop_chat(payload: dict):
    value = payload.get("conversation_id") if isinstance(payload, dict) else None
    try:
        conversation_id = str(UUID(str(value)))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="conversation_id required")
    if not cancel_registry.contains(conversation_id):
        raise HTTPException(status_code=404, detail="Chat generation not running")
    cancel_registry.cancel(conversation_id)
    return {"status": "cancellation_requested", "conversation_id": conversation_id}


@router.get("/conversations")
async def list_conversations(limit: int = Query(20, ge=1, le=100)):
    conversations = await Conversation.all().order_by("-updated_at").limit(limit)
    return {
        "conversations": [
            {
                "id": str(conversation.id),
                "title": conversation.title,
                "created_at": str(conversation.created_at),
                "updated_at": str(conversation.updated_at),
            }
            for conversation in conversations
        ],
        "total": await Conversation.all().count(),
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: UUID):
    conversation = await Conversation.get_or_none(id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = list(
        reversed(await Message.filter(conversation=conversation).order_by("-created_at").limit(50))
    )
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "model_override": conversation.model_override,
        "system_prompt": conversation.system_prompt,
        "created_at": str(conversation.created_at),
        "updated_at": str(conversation.updated_at),
        "messages": [
            {
                "id": str(message.id),
                "role": message.role,
                "content": message.content,
                "model_used": message.model_used,
                "task_type": message.task_type,
                "words_in": message.tokens_in,
                "words_out": message.tokens_out,
                "latency_ms": message.latency_ms,
                "files": message.files or [],
                "created_at": str(message.created_at),
            }
            for message in messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: UUID):
    conversation = await Conversation.get_or_none(id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await conversation.delete()
    return {"status": "deleted", "conversation_id": str(conversation_id)}
