"""Pydantic request/response models for the public API."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """One turn of conversation history sent by the widget."""

    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=20)
    session_id: str | None = Field(default=None, max_length=64)


class Citation(BaseModel):
    """A source chunk that contributed to the answer."""

    document_id: int
    document_name: str
    snippet: str
    score: float


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    session_id: str
    used_documents: int


class DocumentOut(BaseModel):
    id: int
    name: str
    source_type: Literal["pdf", "markdown", "text", "url"]
    chunk_count: int
    char_count: int
    created_at: datetime


class DocumentList(BaseModel):
    documents: list[DocumentOut]
    total_chunks: int


class IngestUrlRequest(BaseModel):
    url: str = Field(..., pattern=r"^https?://.+", max_length=2000)


class EscalateRequest(BaseModel):
    session_id: str = Field(..., min_length=8, max_length=64)
    # Optional contact (email or phone) the user wants to be reached on.
    contact: str | None = Field(default=None, max_length=200)
    # Free-form reason / what they were trying to do.
    reason: str | None = Field(default=None, max_length=1000)


class EscalateResponse(BaseModel):
    id: int
    status: Literal["received"]
    notified: list[str]
    message: str


class AnalyticsResponse(BaseModel):
    """Snapshot of chat-bot usage for the admin dashboard."""

    sessions_total: int
    sessions_today: int
    sessions_7d: int
    messages_total: int
    user_messages_today: int
    user_messages_7d: int
    no_answer_rate_7d: float  # 0.0–1.0; share of bot replies containing "I don't have"
    avg_messages_per_session: float
    escalations_total: int
    escalations_pending: int
    top_questions_7d: list[dict]  # [{"question": "...", "count": 3}]
    daily_volume_30d: list[dict]  # [{"date": "2026-04-25", "messages": 12}]


class HealthResponse(BaseModel):
    status: Literal["ok", "degraded"]
    version: str
    chroma_collection: str
    document_count: int
    chunk_count: int


class ErrorResponse(BaseModel):
    error: str
    detail: str | None = None
