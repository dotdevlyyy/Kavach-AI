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
from app.router.router import model_router
from app.core.ollama_client import ollama_client


router = APIRouter(prefix="/api/chat", tags=["Chat"])


@router.post("")
async def chat_stream_endpoint(request: ChatRequest):
    """
    POST /api/chat
    Streams SSE responses token-by-token with model auto-selection metadata.
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    async def event_generator():
        try:
            # Route model dynamically based on heuristic classifier
            route = await model_router.route_request(
                prompt=request.message,
                file_ids=request.file_ids,
                model_override=request.model_override
            )
            selected_model = route.selected_model

            # Emit metadata event first
            metadata = {
                "conversation_id": conversation_id,
                "model": selected_model,
                "task_type": route.classification.task_type.value,
                "confidence": route.classification.confidence,
                "reasoning": route.routing_reason
            }
            yield f"event: metadata\ndata: {json.dumps(metadata)}\n\n"

            # Construct messages context
            system_prompt = (
                "You are Kavach AI (कवच), a sovereign on-premises AI workbench for "
                "Mangalore Refinery and Petrochemicals Limited (MRPL). You assist refinery "
                "engineers with technical analysis, SOPs, safety standards, inspection reports, "
                "P&ID diagrams, and automated report generation. Provide accurate, professional responses."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.message}
            ]

            # Stream LLM tokens
            async for token in ollama_client.chat_stream(
                model=selected_model,
                messages=messages,
                options={"temperature": 0.4}
            ):
                token_payload = {"token": token}
                yield f"event: token\ndata: {json.dumps(token_payload)}\n\n"

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
    return {
        "conversations": [],
        "total": 0
    }
