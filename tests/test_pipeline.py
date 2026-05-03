"""End-to-end ingestion: bytes → chunks → vector store + metadata DB."""

from __future__ import annotations

import pytest

from app.ingestion.loaders import UnsupportedFileError

pytestmark = pytest.mark.asyncio


SAMPLE_MD = b"""# Hotel Aurora

We are a 24-room boutique hotel.

## Breakfast

Breakfast is served from 07:00 to 10:30 in the dining room.
Coffee is locally roasted. Vegan and gluten-free options available.

## Check-in

Check-in is from 15:00. Check-out is by 11:00.
Late check-out until 14:00 is available for an extra fee.
""" * 3  # multiply so we get more than one chunk at chunk_size=400


async def test_ingest_creates_chunks_and_metadata(pipeline, db, vector_store):
    res = await pipeline.ingest_file(filename="hotel.md", data=SAMPLE_MD)
    assert res.chunks > 1
    assert res.duplicate is False

    docs = await db.list_documents()
    assert len(docs) == 1
    assert docs[0]["name"] == "hotel.md"
    assert docs[0]["chunk_count"] == res.chunks
    assert vector_store.count() == res.chunks


async def test_duplicate_upload_is_skipped(pipeline, db, vector_store):
    first = await pipeline.ingest_file(filename="hotel.md", data=SAMPLE_MD)
    second = await pipeline.ingest_file(filename="hotel.md", data=SAMPLE_MD)
    assert second.duplicate is True
    assert second.document_id == first.document_id
    # The second upload must not double the chunk count.
    assert vector_store.count() == first.chunks


async def test_unsupported_extension_rejected(pipeline):
    with pytest.raises(UnsupportedFileError):
        await pipeline.ingest_file(filename="image.png", data=b"\x89PNG")


async def test_empty_file_rejected(pipeline):
    with pytest.raises(ValueError):
        await pipeline.ingest_file(filename="empty.md", data=b"")


async def test_delete_removes_chunks_and_metadata(pipeline, db, vector_store):
    res = await pipeline.ingest_file(filename="hotel.md", data=SAMPLE_MD)
    assert vector_store.count() > 0
    deleted = await pipeline.delete(res.document_id)
    assert deleted is True
    assert vector_store.count() == 0
    assert await db.list_documents() == []
    # Deleting again is a no-op, not a crash.
    assert await pipeline.delete(res.document_id) is False


async def test_query_returns_relevant_chunk(pipeline, vector_store):
    await pipeline.ingest_file(filename="hotel.md", data=SAMPLE_MD)
    hits = vector_store.query("What time is breakfast?", top_k=2)
    assert hits, "expected at least one retrieved chunk"
    top = hits[0]
    # The breakfast paragraph mentions 07:00 — the top hit should contain it.
    assert "breakfast" in top.text.lower() or "07:00" in top.text
    assert 0.0 <= top.score <= 1.0
    assert top.document_name == "hotel.md"
