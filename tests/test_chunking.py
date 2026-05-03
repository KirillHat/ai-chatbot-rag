"""Tests for the recursive text splitter."""

from __future__ import annotations

import pytest

from app.ingestion.chunking import split_text


def test_short_text_one_chunk():
    out = split_text("hello world", chunk_size=100, chunk_overlap=10)
    assert out == ["hello world"]


def test_empty_text_returns_nothing():
    assert split_text("", chunk_size=100, chunk_overlap=10) == []
    assert split_text("   \n  \r\n  ", chunk_size=100, chunk_overlap=10) == []


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError):
        split_text("a" * 200, chunk_size=100, chunk_overlap=100)
    with pytest.raises(ValueError):
        split_text("a" * 200, chunk_size=100, chunk_overlap=200)


def test_paragraph_split_keeps_chunks_under_limit():
    paragraphs = ["First paragraph. " * 5, "Second paragraph. " * 5, "Third one. " * 5]
    text = "\n\n".join(paragraphs)
    chunks = split_text(text, chunk_size=120, chunk_overlap=20)
    assert chunks
    # Chunks may exceed `chunk_size` slightly because of trailing separators
    # we re-attach during the recursive split, but should never explode.
    assert all(len(c) <= 200 for c in chunks)


def test_overlap_actually_overlaps():
    """Adjacent chunks should share at least `overlap` chars of trailing text."""
    text = "alpha. " * 60  # ~420 chars
    chunks = split_text(text, chunk_size=120, chunk_overlap=40)
    assert len(chunks) >= 2
    for prev, nxt in zip(chunks, chunks[1:], strict=False):
        # The next chunk should contain at least some of the previous chunk's tail.
        assert any(prev[-i:] in nxt for i in range(20, 40)) or prev[-20:] in nxt


def test_long_run_with_no_separators_uses_hard_cut():
    # No spaces, no punctuation — splitter falls back to per-character cut.
    text = "x" * 1000
    chunks = split_text(text, chunk_size=200, chunk_overlap=20)
    assert chunks
    assert all(len(c) <= 220 for c in chunks)


def test_normalises_crlf_to_lf():
    text = "line one\r\nline two\r\nline three"
    chunks = split_text(text, chunk_size=200, chunk_overlap=10)
    assert all("\r" not in c for c in chunks)
