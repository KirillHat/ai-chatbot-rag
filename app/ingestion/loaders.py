"""File-format loaders.

Each loader returns plain text. Heavy parsers (Office docs, scanned PDFs
needing OCR) are intentionally out of scope — extending the dispatch table
in `load_bytes` is the natural place to add them.
"""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader

# A pragmatic upper bound for one upload — keeps memory predictable and
# protects the embedder from a single 500-page book that would tie it up
# for minutes. Tune in production if you genuinely need bigger uploads.
MAX_BYTES = 25 * 1024 * 1024  # 25 MB
SUPPORTED_EXTENSIONS = {".pdf", ".md", ".markdown", ".txt"}


class UnsupportedFileError(ValueError):
    pass


class FileTooLargeError(ValueError):
    pass


def detect_source_type(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return "pdf"
    if ext in (".md", ".markdown"):
        return "markdown"
    if ext == ".txt":
        return "text"
    raise UnsupportedFileError(
        f"Unsupported extension {ext!r}. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
    )


def _load_pdf(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception:
            # Fonts that pypdf can't decode shouldn't fail the whole upload.
            pages.append("")
    return "\n\n".join(pages).strip()


def _load_text(data: bytes) -> str:
    # Try UTF-8 first, fall back to latin-1 — between them they cover ~all
    # PDFs/Markdown emitted by office tools.
    for enc in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return data.decode(enc).strip()
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore").strip()


def load_bytes(filename: str, data: bytes) -> tuple[str, str]:
    """Detect source type and decode the bytes to plain text.

    Returns (text, source_type).
    """
    if len(data) > MAX_BYTES:
        raise FileTooLargeError(
            f"File is {len(data) / 1_048_576:.1f} MB, max is {MAX_BYTES / 1_048_576:.0f} MB"
        )
    source_type = detect_source_type(filename)
    if source_type == "pdf":
        return _load_pdf(data), source_type
    return _load_text(data), source_type
