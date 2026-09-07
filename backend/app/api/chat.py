"""
Kavach AI — Chat API Endpoints
Provides real-time streaming chat with automatic model routing and conversation management.
"""

import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from loguru import logger

from app.schemas.chat import ChatRequest
from app.router.router import route_request
from app.core.ollama_client import ollama_client
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

    # Ensure conversation exists in DB
    conversation, _ = await Conversation.get_or_create(
        id=conversation_id,
        defaults={"title": request.message[:80]}
    )

    # Persist user message
    await Message.create(
        conversation=conversation,
        role="user",
        content=request.message,
    )

    async def event_generator():
        full_response = ""
        try:
            # Route model dynamically based on heuristic classifier
            selected_model, route_metadata = route_request(
                message=request.message,
                model_override=request.model_override
            )

            # Emit metadata event first
            metadata = {
                "conversation_id": conversation_id,
                "model": selected_model,
                "task_type": route_metadata.task_type,
                "confidence": route_metadata.confidence,
                "reasoning": route_metadata.reasoning
            }
            yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

            # Construct messages context
            system_prompt = (
                "You are Kavach AI (कवच), a sovereign on-premises AI workbench for "
                "Mangalore Refinery and Petrochemicals Limited (MRPL). You assist refinery "
                "engineers with technical analysis, SOPs, safety standards, inspection reports, "
                "P&ID diagrams, and automated report generation. Provide accurate, professional responses."
            )

            # Load recent conversation history for context
            recent_messages = await Message.filter(
                conversation=conversation
            ).order_by("created_at").limit(20)

            messages = [{"role": "system", "content": system_prompt}]
            for msg in recent_messages:
                messages.append({"role": msg.role, "content": msg.content})

            # Stream LLM tokens
            async for chunk in ollama_client.chat_stream(
                model=selected_model,
                messages=messages,
                options={"temperature": 0.4}
            ):
                token_text = chunk.message.content if hasattr(chunk, 'message') else chunk.get("message", {}).get("content", "")
                if token_text:
                    full_response += token_text
                    yield f"event: token\ndata: {json.dumps({'token': token_text})}\n\n"

            # Persist assistant response
            await Message.create(
                conversation=conversation,
                role="assistant",
                content=full_response,
            )

            # Update conversation title if it was just created
            if conversation.title == request.message[:80] and full_response:
                conversation.title = request.message[:80]
                await conversation.save()

            # Emit done event
            done_payload = {"conversation_id": conversation_id, "status": "completed"}
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            logger.error(f"Error in chat streaming endpoint: {e}")
            error_payload = {"error": str(e)}
            yield f"event: error\ndata: {json.dumps(error_payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


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
                "is_agent_mode": c.is_agent_mode,
                "created_at": str(c.created_at),
                "updated_at": str(c.updated_at),
            }
            for c in conversations
        ],
        "total": await Conversation.all().count()
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

