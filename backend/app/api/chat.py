"""
Kavach AI — Chat API Endpoints
Provides real-time streaming chat with automatic model routing and conversation management.
"""

import uuid
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from app.schemas.chat import ChatRequest
from app.rag.retriever import hybrid_search
from app.router.router import route_request
from app.core.ollama_client import ollama_client
from app.core.cancellation import registry as cancel_registry
from app.core.sse import sse
from app.models.conversation import Conversation
from app.models.message import Message


router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("")
async def chat_stream_endpoint(request: ChatRequest):
    """
    POST /api/chat
    Streams SSE responses token-by-token with model auto-selection metadata.
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())
    file_ids = request.file_ids or request.files

    # Ensure conversation exists in DB
    conversation, created = await Conversation.get_or_create(
        id=conversation_id,
        defaults={
            "title": request.message[:80],
            "model_override": request.model_override,
            "system_prompt": request.system_prompt,
        },
    )

    cancel_event = cancel_registry.get(conversation_id)

    async def event_generator():
        import time
        full_response = ""
        t0 = time.monotonic()
        try:
            # Snapshot history BEFORE inserting the new user turn, so the explicit
            # `messages.append({user, ...})` below is the authoritative user message.
            history = await Message.filter(
                conversation=conversation
            ).order_by("created_at").limit(20)

            # Persist user message (after history snapshot)
            user_msg = await Message.create(
                conversation=conversation,
                role="user",
                content=request.message,
                files=list(file_ids),
            )

            # Route model dynamically based on heuristic classifier
            selected_model, route_metadata = await route_request(
                message=request.message,
                file_ids=file_ids,
                model_override=request.model_override,
            )

            # Emit metadata event first
            metadata = {
                "conversation_id": conversation_id,
                "message_id": str(user_msg.id),
                "model": selected_model,
                "task_type": route_metadata.task_type,
                "confidence": route_metadata.confidence,
                "reasoning": route_metadata.reasoning,
            }
            yield sse("metadata", metadata)

            system_prompt = (
                request.system_prompt
                if request.system_prompt
                else (
                    "You are Kavach AI (कवच), a sovereign on-premises AI workbench for "
                    "Mangalore Refinery and Petrochemicals Limited (MRPL). You assist refinery "
                    "engineers with technical analysis, SOPs, safety standards, inspection reports, "
                    "P&ID diagrams, and automated report generation. Provide accurate, professional responses."
                )
            )

            messages = [{"role": "system", "content": system_prompt}]
            for msg in history:
                messages.append({"role": msg.role, "content": msg.content})
            messages.append({"role": "user", "content": request.message})

            # KB context injection: when flag is on, prepend top-K hybrid hits as a system message.
            # Skip the embedding call entirely when Ollama is unreachable — vector search would
            # just spam errors and FTS alone covers the offline path.
            if request.enable_knowledge_base:
                try:
                    healthy, _ = await ollama_client.is_healthy()
                    if healthy:
                        kb_hits = await hybrid_search(request.message, limit=3)
                        if kb_hits:
                            context_lines = [
                                f"[{h.get('document_name', 'KB')}] {h['content'][:400]}"
                                for h in kb_hits
                            ]
                            messages.insert(1, {
                                "role": "system",
                                "content": "Knowledge base context:\n" + "\n".join(context_lines),
                            })
                except Exception as e:
                    logger.warning(f"KB context retrieval failed: {e}")

            # Approximate word count; Ollama SDK does not expose real tokenizer counts.
            words_in = sum(len(m["content"].split()) for m in messages)

            # Stream LLM tokens
            async for chunk in ollama_client.chat_stream(
                model=selected_model,
                messages=messages,
                keep_alive=-1,
                options={"temperature": 0.4},
            ):
                if cancel_event.is_set():
                    yield sse("stopped", {'conversation_id': conversation_id})
                    break
                token_text = chunk.message.content if hasattr(chunk, 'message') else chunk.get("message", {}).get("content", "")
                if token_text:
                    full_response += token_text
                    yield sse("token", {'content': token_text, 'token': token_text})

            latency_ms = int((time.monotonic() - t0) * 1000)
            words_out = len(full_response.split())

            # Persist assistant response
            assistant_msg = await Message.create(
                conversation=conversation,
                role="assistant",
                content=full_response,
                model_used=selected_model,
                task_type=route_metadata.task_type,
                tokens_in=words_in,
                tokens_out=words_out,
                latency_ms=latency_ms,
            )

            # Emit done event
            done_payload = {
                "conversation_id": conversation_id,
                "message_id": str(user_msg.id),
                "assistant_message_id": str(assistant_msg.id),
                "model": selected_model,
                "status": "stopped" if cancel_event.is_set() else "completed",
                "words_in": words_in,
                "words_out": words_out,
            }
            yield sse("done", done_payload)

        except Exception as e:
            logger.error(f"Error in chat streaming endpoint: {e}")
            error_payload = {"error": str(e)}
            yield sse("error", error_payload)
        finally:
            cancel_registry.clear(conversation_id)

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/stop")
async def stop_chat(payload: dict):
    """
    POST /api/chat/stop
    Signal cancellation for an in-progress chat stream.
    Body: {"conversation_id": "..."}
    """
    cid = payload.get("conversation_id") if isinstance(payload, dict) else None
    if not cid:
        raise HTTPException(status_code=400, detail="conversation_id required")
    cancel_registry.cancel(cid)
    return {"status": "cancellation_requested", "conversation_id": cid}


@router.get("/conversations")
async def list_conversations(limit: int = Query(20, ge=1, le=100)):
    """
    GET /api/chat/conversations
    Returns list of recent chat conversations.
    """
    conversations = await Conversation.all().order_by("-updated_at").limit(limit)
    return {
        "conversations": [
            {
                "id": str(c.id),
                "title": c.title,
                "created_at": str(c.created_at),
                "updated_at": str(c.updated_at),
            }
            for c in conversations
        ],
        "total": len(conversations),
    }


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """
    GET /api/chat/conversations/{id}
    Fetch a conversation with all its messages.
    """
    conversation = await Conversation.get_or_none(id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = await Message.filter(conversation=conversation).order_by("created_at").limit(50)
    return {
        "id": str(conversation.id),
        "title": conversation.title,
        "model_override": conversation.model_override,
        "system_prompt": conversation.system_prompt,
        "created_at": str(conversation.created_at),
        "updated_at": str(conversation.updated_at),
        "messages": [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "model_used": m.model_used,
                "task_type": m.task_type,
                "words_in": m.tokens_in,  # words, not tokens (V3-3)
                "words_out": m.tokens_out,  # words, not tokens (V3-3)
                "latency_ms": m.latency_ms,
                "files": m.files or [],
                "created_at": str(m.created_at),
            }
            for m in messages
        ],
    }


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """DELETE /api/chat/conversations/{id} — Delete a conversation and its messages."""
    conversation = await Conversation.get_or_none(id=conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    await Message.filter(conversation=conversation).delete()
    await conversation.delete()
    return {"status": "deleted", "conversation_id": conversation_id}

