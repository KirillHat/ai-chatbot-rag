"""Async SQLite layer."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_init_is_idempotent(db):
    # Calling init() twice on the same DB should not error.
    await db.init()
    await db.init()
    assert await db.list_documents() == []


async def test_add_and_list_documents(db):
    doc_id = await db.add_document(
        name="hello.md",
        source_type="markdown",
        chunk_count=4,
        char_count=1000,
        file_path="/tmp/hello.md",
        sha256="abc123",
    )
    assert doc_id > 0
    docs = await db.list_documents()
    assert len(docs) == 1
    assert docs[0]["name"] == "hello.md"
    assert docs[0]["chunk_count"] == 4

    fetched = await db.get_document(doc_id)
    assert fetched is not None
    assert fetched["sha256"] == "abc123"


async def test_get_by_sha(db):
    await db.add_document(
        name="a.md", source_type="markdown",
        chunk_count=1, char_count=10, file_path=None, sha256="deadbeef",
    )
    found = await db.get_document_by_sha("deadbeef")
    assert found is not None
    assert found["name"] == "a.md"
    assert await db.get_document_by_sha("nope") is None


async def test_total_chunks_sums_up(db):
    await db.add_document(
        name="a.md", source_type="markdown",
        chunk_count=3, char_count=10, file_path=None, sha256="s1",
    )
    await db.add_document(
        name="b.md", source_type="markdown",
        chunk_count=7, char_count=10, file_path=None, sha256="s2",
    )
    assert await db.total_chunks() == 10


async def test_delete_document(db):
    doc_id = await db.add_document(
        name="x.md", source_type="markdown",
        chunk_count=1, char_count=10, file_path=None, sha256="s",
    )
    assert await db.delete_document(doc_id) is True
    assert await db.delete_document(doc_id) is False
    assert await db.list_documents() == []


async def test_chat_session_and_messages(db):
    sid = "session-1"
    await db.upsert_session(sid, user_agent="pytest")
    await db.log_message(session_id=sid, role="user", content="Hi")
    await db.log_message(
        session_id=sid,
        role="assistant",
        content="Hello",
        citations=[{"document_id": 1, "document_name": "a.md"}],
    )
    # Re-upserting the same session should not error or duplicate.
    await db.upsert_session(sid)
