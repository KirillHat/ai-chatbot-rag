"""Admin endpoints: upload, list, and delete knowledge-base documents."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, Response, UploadFile, status

from app.api.deps import get_db, get_ingestion, require_admin
from app.db.database import Database
from app.ingestion.loaders import (
    SUPPORTED_EXTENSIONS,
    FileTooLargeError,
    UnsupportedFileError,
)
from app.ingestion.pipeline import IngestionPipeline
from app.models.schemas import AnalyticsResponse, DocumentList, DocumentOut

router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)
log = logging.getLogger(__name__)


def _row_to_out(row: dict) -> DocumentOut:
    created_raw = row["created_at"]
    if isinstance(created_raw, str):
        try:
            created = datetime.fromisoformat(created_raw)
        except ValueError:
            # SQLite default is 'YYYY-MM-DD HH:MM:SS' — coerce to ISO.
            created = datetime.fromisoformat(created_raw.replace(" ", "T"))
    else:
        created = created_raw
    return DocumentOut(
        id=row["id"],
        name=row["name"],
        source_type=row["source_type"],
        chunk_count=row["chunk_count"],
        char_count=row["char_count"],
        created_at=created,
    )


@router.get("/documents", response_model=DocumentList)
async def list_documents(db: Annotated[Database, Depends(get_db)]) -> DocumentList:
    rows = await db.list_documents()
    total = await db.total_chunks()
    return DocumentList(
        documents=[_row_to_out(r) for r in rows],
        total_chunks=total,
    )


@router.post(
    "/documents",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
)
async def upload_document(
    ingestion: Annotated[IngestionPipeline, Depends(get_ingestion)],
    db: Annotated[Database, Depends(get_db)],
    file: UploadFile = File(...),
) -> DocumentOut:
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing filename",
        )

    data = await file.read()
    try:
        result = await ingestion.ingest_file(filename=file.filename, data=data)
    except UnsupportedFileError as e:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"{e} (supported: {sorted(SUPPORTED_EXTENSIONS)})",
        ) from e
    except FileTooLargeError as e:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(e),
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e
    except Exception as e:
        log.exception("Upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to ingest the document",
        ) from e

    row = await db.get_document(result.document_id)
    if row is None:
        raise HTTPException(status_code=500, detail="Inconsistent state after upload")
    return _row_to_out(row)


@router.get("/analytics", response_model=AnalyticsResponse)
async def analytics(db: Annotated[Database, Depends(get_db)]) -> AnalyticsResponse:
    """Aggregated chat/escalation metrics for the admin dashboard.

    Everything is computed from existing tables (`chat_sessions`,
    `chat_messages`, `escalations`) — no separate analytics store.
    Cheap up to ~100k messages because we run inside SQLite and the
    indexes on (session_id, status, created_at) cover every filter.
    """
    import aiosqlite

    sql_one = lambda c: c.fetchone()  # noqa: E731

    async with aiosqlite.connect(db.path) as conn:
        conn.row_factory = aiosqlite.Row

        async def scalar(query: str, *args) -> int:
            cur = await conn.execute(query, args)
            row = await sql_one(cur)
            return int(row[0]) if row and row[0] is not None else 0

        sessions_total = await scalar("SELECT COUNT(*) FROM chat_sessions")
        sessions_today = await scalar(
            "SELECT COUNT(*) FROM chat_sessions WHERE created_at >= datetime('now','-1 day')"
        )
        sessions_7d = await scalar(
            "SELECT COUNT(*) FROM chat_sessions WHERE created_at >= datetime('now','-7 days')"
        )
        messages_total = await scalar("SELECT COUNT(*) FROM chat_messages")
        user_today = await scalar(
            "SELECT COUNT(*) FROM chat_messages WHERE role='user' AND created_at >= datetime('now','-1 day')"
        )
        user_7d = await scalar(
            "SELECT COUNT(*) FROM chat_messages WHERE role='user' AND created_at >= datetime('now','-7 days')"
        )
        # No-answer rate: bot replies whose content suggests a refusal.
        # Cheap heuristic — a real product would tag refusals server-side
        # (see TODO in chat_service.py). Patterns cover:
        #   - English (with both straight ' and curly ' apostrophes)
        #   - Russian, Spanish, German, French refusal vocabulary
        #   - the literal "(error)" marker we write on RAG failures
        no_answer_7d = await scalar(
            "SELECT COUNT(*) FROM chat_messages WHERE role='assistant' "
            "AND created_at >= datetime('now','-7 days') AND ("
            "  lower(content) LIKE '%don''t have%'      OR"  # don't / don't (curly handled below)
            "  lower(content) LIKE '%don’t have%'   OR"
            "  lower(content) LIKE '%dont have%'         OR"
            "  lower(content) LIKE '%no information%'    OR"
            "  lower(content) LIKE '%(error)%'           OR"
            "  lower(content) LIKE '%у меня нет%'        OR"  # ru
            "  lower(content) LIKE '%не могу ответить%'  OR"  # ru
            "  lower(content) LIKE '%no tengo informaci%'OR"  # es
            "  lower(content) LIKE '%no puedo respond%'  OR"  # es
            "  lower(content) LIKE '%keine information%' OR"  # de
            "  lower(content) LIKE '%je n''ai pas%'      OR"  # fr
            "  lower(content) LIKE '%je ne peux pas%')"      # fr
        )
        bot_7d = await scalar(
            "SELECT COUNT(*) FROM chat_messages WHERE role='assistant' "
            "AND created_at >= datetime('now','-7 days')"
        )
        no_answer_rate = round(no_answer_7d / bot_7d, 4) if bot_7d > 0 else 0.0

        avg_msgs = 0.0
        if sessions_total > 0:
            avg_msgs = round(messages_total / sessions_total, 2)

        # Top user questions (last 7 days). Trim to 80 chars and group case-insensitively.
        cur = await conn.execute(
            """
            SELECT substr(lower(content), 1, 80) AS q, COUNT(*) AS c
            FROM chat_messages
            WHERE role='user' AND created_at >= datetime('now','-7 days')
            GROUP BY q
            ORDER BY c DESC
            LIMIT 5
            """
        )
        top_questions = [dict(r) for r in await cur.fetchall()]
        top_questions = [{"question": r["q"], "count": r["c"]} for r in top_questions]

        # Daily volume for the last 30 days. Empty days are filled in with 0
        # so the dashboard can render a smooth bar chart without gaps.
        cur = await conn.execute(
            """
            SELECT date(created_at) AS d, COUNT(*) AS c
            FROM chat_messages
            WHERE role='user' AND created_at >= datetime('now','-30 days')
            GROUP BY d ORDER BY d
            """
        )
        rows = await cur.fetchall()
        by_date = {r["d"]: r["c"] for r in rows}
        from datetime import datetime, timedelta, timezone

        today = datetime.now(timezone.utc).date()
        daily_volume = []
        for i in range(29, -1, -1):
            d = (today - timedelta(days=i)).isoformat()
            daily_volume.append({"date": d, "messages": int(by_date.get(d, 0))})

        escalations_total = await scalar("SELECT COUNT(*) FROM escalations")
        escalations_pending = await scalar(
            "SELECT COUNT(*) FROM escalations WHERE status = 'pending'"
        )

    return AnalyticsResponse(
        sessions_total=sessions_total,
        sessions_today=sessions_today,
        sessions_7d=sessions_7d,
        messages_total=messages_total,
        user_messages_today=user_today,
        user_messages_7d=user_7d,
        no_answer_rate_7d=no_answer_rate,
        avg_messages_per_session=avg_msgs,
        escalations_total=escalations_total,
        escalations_pending=escalations_pending,
        top_questions_7d=top_questions,
        daily_volume_30d=daily_volume,
    )


@router.delete(
    "/documents/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_document(
    doc_id: int,
    ingestion: Annotated[IngestionPipeline, Depends(get_ingestion)],
) -> Response:
    deleted = await ingestion.delete(doc_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {doc_id} not found",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
