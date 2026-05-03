"""Public chat endpoints — called from the embeddable widget.

Two flavors share the same request schema:

  * `POST /api/chat`        — one-shot, returns the full answer in JSON.
  * `POST /api/chat/stream` — Server-Sent Events stream of text deltas,
                              followed by citations + done events.

Both go through the same RAG pipeline; streaming just changes the way the
final text is delivered. Citations can only be assembled after the model
finishes (we need to parse [n] markers from the full text), so they
arrive AFTER the deltas, before the `done` event.
"""

from __future__ import annotations

import json
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.api.deps import get_chat, rate_limit
from app.models.schemas import ChatRequest, ChatResponse, Citation
from app.services.chat_service import ChatService

router = APIRouter(prefix="/api", tags=["chat"], dependencies=[Depends(rate_limit)])
log = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    request: Request,
    chat_service: Annotated[ChatService, Depends(get_chat)],
) -> ChatResponse:
    user_agent = request.headers.get("user-agent")
    try:
        answer, citations, session_id, used_docs = await chat_service.reply(
            message=payload.message,
            history=payload.history,
            session_id=payload.session_id,
            user_agent=user_agent,
        )
    except RuntimeError as e:
        # ANTHROPIC_API_KEY missing — return a friendly 503 the widget can display.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        ) from e
    except Exception as e:
        log.exception("Chat handler failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Chat backend failed — please try again",
        ) from e

    return ChatResponse(
        answer=answer,
        citations=citations,
        session_id=session_id,
        used_documents=used_docs,
    )


def _sse(event: dict) -> bytes:
    """Format one Server-Sent Events frame."""
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n".encode()


@router.post("/chat/stream")
async def chat_stream(
    payload: ChatRequest,
    request: Request,
    chat_service: Annotated[ChatService, Depends(get_chat)],
) -> StreamingResponse:
    """Stream the answer as Server-Sent Events.

    Event shapes the widget consumes:
      {"type": "delta",     "text": "..."}            (many)
      {"type": "citations", "citations": [...]}       (one)
      {"type": "done",      "session_id": "...",
                            "used_documents": N}      (one)
      {"type": "error",     "message": "..."}         (only on failure)

    The endpoint runs the full RAG pipeline streaming-end-to-end:
    retrieval is sync, deltas come from Claude's stream API, and
    citations are parsed from the accumulated text after the stream
    completes. The session is logged the same way as the non-streaming
    path so analytics work identically.
    """
    user_agent = request.headers.get("user-agent")

    async def event_source():
        try:
            async for ev in chat_service.stream_reply(
                message=payload.message,
                history=payload.history,
                session_id=payload.session_id,
                user_agent=user_agent,
            ):
                yield _sse(ev)
        except RuntimeError as e:
            # API key missing — surface as a clean error event so the
            # widget can show a friendly toast instead of HTTP 503 mid-stream.
            yield _sse({"type": "error", "message": str(e), "fatal": True})
        except Exception:
            log.exception("Streaming chat handler failed")
            yield _sse({"type": "error", "message": "Chat backend failed — please try again."})

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",  # disable nginx response buffering
            "Connection": "keep-alive",
        },
    )


def _citation_payload(c: Citation) -> dict:
    return c.model_dump()
