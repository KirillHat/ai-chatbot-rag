"""Health and metadata endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request

from app import __version__
from app.api.deps import get_db
from app.db.database import Database
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(
    request: Request,
    db: Annotated[Database, Depends(get_db)],
) -> HealthResponse:
    vs = request.app.state.vector_store
    chunk_count = await db.total_chunks()
    docs = await db.list_documents()
    return HealthResponse(
        status="ok" if request.app.state.claude.configured else "degraded",
        version=__version__,
        chroma_collection=vs.collection_name,
        document_count=len(docs),
        chunk_count=chunk_count,
    )
