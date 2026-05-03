"""Async SQLite layer for document and chat-session metadata.

The vector data lives in Chroma; SQLite is only the source of truth for
human-readable metadata (file name, upload time, chunk count) and
conversation logs. This split keeps the vector store hot-swappable —
swap Chroma for Qdrant or pgvector and SQLite stays unchanged.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite

SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    source_type  TEXT NOT NULL CHECK (source_type IN ('pdf', 'markdown', 'text', 'url')),
    chunk_count  INTEGER NOT NULL DEFAULT 0,
    char_count   INTEGER NOT NULL DEFAULT 0,
    file_path    TEXT,
    sha256       TEXT,
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_documents_sha256 ON documents(sha256);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id           TEXT PRIMARY KEY,
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at   TEXT NOT NULL DEFAULT (datetime('now')),
    user_agent   TEXT
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role         TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content      TEXT NOT NULL,
    citations    TEXT,  -- JSON
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_session ON chat_messages(session_id);

CREATE TABLE IF NOT EXISTS escalations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id   TEXT NOT NULL,
    contact      TEXT,
    reason       TEXT,
    transcript   TEXT,
    status       TEXT NOT NULL DEFAULT 'pending'
                 CHECK (status IN ('pending', 'notified', 'closed')),
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_escalations_status ON escalations(status);
CREATE INDEX IF NOT EXISTS idx_escalations_created ON escalations(created_at);
"""


class Database:
    """Thin async wrapper around aiosqlite for the metadata tables."""

    def __init__(self, path: Path):
        self.path = Path(path)

    async def init(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.execute("PRAGMA foreign_keys = ON")
            await db.executescript(SCHEMA)
            await db.commit()

    @asynccontextmanager
    async def _conn(self) -> AsyncIterator[aiosqlite.Connection]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            await db.execute("PRAGMA foreign_keys = ON")
            yield db

    # --- Documents ---

    async def add_document(
        self,
        *,
        name: str,
        source_type: str,
        chunk_count: int,
        char_count: int,
        file_path: str | None,
        sha256: str | None,
    ) -> int:
        async with self._conn() as db:
            cur = await db.execute(
                """
                INSERT INTO documents (name, source_type, chunk_count, char_count, file_path, sha256)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, source_type, chunk_count, char_count, file_path, sha256),
            )
            await db.commit()
            return cur.lastrowid or 0

    async def list_documents(self) -> list[dict[str, Any]]:
        async with self._conn() as db:
            cur = await db.execute(
                "SELECT id, name, source_type, chunk_count, char_count, created_at "
                "FROM documents ORDER BY id DESC"
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def get_document(self, doc_id: int) -> dict[str, Any] | None:
        async with self._conn() as db:
            cur = await db.execute(
                "SELECT id, name, source_type, chunk_count, char_count, file_path, sha256, created_at "
                "FROM documents WHERE id = ?",
                (doc_id,),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def get_document_by_sha(self, sha256: str) -> dict[str, Any] | None:
        async with self._conn() as db:
            cur = await db.execute(
                "SELECT id, name, source_type, chunk_count, char_count, file_path, sha256, created_at "
                "FROM documents WHERE sha256 = ?",
                (sha256,),
            )
            row = await cur.fetchone()
            return dict(row) if row else None

    async def delete_document(self, doc_id: int) -> bool:
        async with self._conn() as db:
            cur = await db.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
            await db.commit()
            return (cur.rowcount or 0) > 0

    async def total_chunks(self) -> int:
        async with self._conn() as db:
            cur = await db.execute("SELECT COALESCE(SUM(chunk_count), 0) AS n FROM documents")
            row = await cur.fetchone()
            return int(row["n"]) if row else 0

    # --- Chat sessions ---

    async def session_exists(self, session_id: str) -> bool:
        async with self._conn() as db:
            cur = await db.execute(
                "SELECT 1 FROM chat_sessions WHERE id = ? LIMIT 1",
                (session_id,),
            )
            row = await cur.fetchone()
            return row is not None

    async def upsert_session(self, session_id: str, user_agent: str | None = None) -> None:
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        async with self._conn() as db:
            await db.execute(
                """
                INSERT INTO chat_sessions (id, user_agent, created_at, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (session_id, user_agent, now, now),
            )
            await db.commit()

    async def fetch_transcript(self, session_id: str, *, limit: int = 50) -> list[dict[str, Any]]:
        async with self._conn() as db:
            cur = await db.execute(
                "SELECT role, content, created_at FROM chat_messages "
                "WHERE session_id = ? ORDER BY id ASC LIMIT ?",
                (session_id, limit),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def add_escalation(
        self,
        *,
        session_id: str,
        contact: str | None,
        reason: str | None,
        transcript: str | None,
        status: str = "pending",
    ) -> int:
        async with self._conn() as db:
            cur = await db.execute(
                """
                INSERT INTO escalations (session_id, contact, reason, transcript, status)
                VALUES (?, ?, ?, ?, ?)
                """,
                (session_id, contact, reason, transcript, status),
            )
            await db.commit()
            return cur.lastrowid or 0

    async def list_escalations(self, *, limit: int = 50) -> list[dict[str, Any]]:
        async with self._conn() as db:
            cur = await db.execute(
                "SELECT id, session_id, contact, reason, status, created_at "
                "FROM escalations ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            rows = await cur.fetchall()
            return [dict(r) for r in rows]

    async def log_message(
        self,
        *,
        session_id: str,
        role: str,
        content: str,
        citations: list[dict] | None = None,
    ) -> None:
        async with self._conn() as db:
            await db.execute(
                """
                INSERT INTO chat_messages (session_id, role, content, citations)
                VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    role,
                    content,
                    json.dumps(citations) if citations else None,
                ),
            )
            await db.commit()
