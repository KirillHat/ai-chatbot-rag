"""Text → chunks.

A small recursive splitter — roughly the same algorithm as LangChain's
RecursiveCharacterTextSplitter, reimplemented to drop the dependency.
We split on the largest separator that fits (paragraphs → lines →
sentences → words → chars), then merge adjacent pieces back together
until each chunk is close to `chunk_size`. Adjacent chunks share
`chunk_overlap` characters so a fact straddling a chunk boundary still
shows up in retrieval.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

# Order matters — bigger boundaries first.
SEPARATORS: tuple[str, ...] = (
    "\n\n",
    "\n",
    ". ",
    "? ",
    "! ",
    "; ",
    ", ",
    " ",
    "",
)


def _split_with_separator(text: str, sep: str) -> list[str]:
    if sep == "":
        return list(text)
    parts = text.split(sep)
    # Re-attach the separator to every fragment except the last so we don't
    # silently swallow whitespace boundaries.
    out = [p + sep for p in parts[:-1]]
    if parts[-1]:
        out.append(parts[-1])
    return out


def _recursive_split(text: str, chunk_size: int, separators: tuple[str, ...]) -> list[str]:
    if len(text) <= chunk_size:
        return [text]
    if not separators:
        # Hard cut as a last resort.
        return [text[i : i + chunk_size] for i in range(0, len(text), chunk_size)]

    sep, *rest = separators
    parts = _split_with_separator(text, sep)

    chunks: list[str] = []
    for part in parts:
        if len(part) <= chunk_size:
            chunks.append(part)
        else:
            chunks.extend(_recursive_split(part, chunk_size, tuple(rest)))
    return chunks


def _merge_with_overlap(
    parts: Iterable[str], chunk_size: int, overlap: int
) -> list[str]:
    parts = [p for p in parts if p]
    if not parts:
        return []

    merged: list[str] = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) <= chunk_size:
            buf += part
            continue
        if buf:
            merged.append(buf.strip())
        # Carry overlap from the previous buffer to keep context across boundaries.
        if overlap and merged:
            tail = merged[-1][-overlap:]
            buf = tail + part
        else:
            buf = part
    if buf:
        merged.append(buf.strip())
    return [c for c in merged if c]


def split_text(
    text: str,
    *,
    chunk_size: int,
    chunk_overlap: int,
) -> list[str]:
    """Split a body of text into overlapping ~chunk_size pieces."""
    text = re.sub(r"\r\n?", "\n", text or "").strip()
    if not text:
        return []
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    parts = _recursive_split(text, chunk_size, SEPARATORS)
    return _merge_with_overlap(parts, chunk_size, chunk_overlap)
