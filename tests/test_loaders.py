"""Tests for the file loaders + format detection."""

from __future__ import annotations

import pytest

from app.ingestion.loaders import (
    FileTooLargeError,
    UnsupportedFileError,
    detect_source_type,
    load_bytes,
)


def test_detects_extensions():
    assert detect_source_type("file.pdf") == "pdf"
    assert detect_source_type("file.PDF") == "pdf"
    assert detect_source_type("notes.md") == "markdown"
    assert detect_source_type("notes.markdown") == "markdown"
    assert detect_source_type("readme.txt") == "text"


def test_rejects_unsupported_extension():
    with pytest.raises(UnsupportedFileError):
        detect_source_type("image.png")


def test_loads_markdown_text():
    text = "# Title\n\nSome content here."
    body, source = load_bytes("doc.md", text.encode("utf-8"))
    assert source == "markdown"
    assert "Title" in body
    assert "Some content" in body


def test_loads_plain_text():
    body, source = load_bytes("notes.txt", b"plain text content")
    assert source == "text"
    assert body == "plain text content"


def test_loads_utf8_with_bom():
    body, _ = load_bytes("notes.md", "﻿# Title".encode())
    assert "Title" in body


def test_falls_back_to_latin1_for_non_utf8():
    # Pure latin-1 byte that is not valid UTF-8.
    body, _ = load_bytes("notes.md", b"caf\xe9")
    assert "caf" in body


def test_too_large_raises():
    huge = b"x" * (26 * 1024 * 1024)
    with pytest.raises(FileTooLargeError):
        load_bytes("big.txt", huge)
