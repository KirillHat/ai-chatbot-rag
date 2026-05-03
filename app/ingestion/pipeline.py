"""End-to-end ingestion: bytes → chunks → vector store + metadata DB."""

from __future__ import annotations

import contextlib
import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

from app.core.vectorstore import VectorStore
from app.db.database import Database
from app.ingestion.chunking import split_text
from app.ingestion.loaders import load_bytes

log = logging.getLogger(__name__)


@dataclass
class IngestResult:
    document_id: int
    name: str
    source_type: str
    chunks: int
    chars: int
    duplicate: bool


class IngestionPipeline:
    def __init__(
        self,
        *,
        db: Database,
        vector_store: VectorStore,
        upload_dir: Path,
        chunk_size: int,
        chunk_overlap: int,
        on_change=None,
    ):
        self.db = db
        self.vector_store = vector_store
        self.upload_dir = Path(upload_dir)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # Optional callback fired AFTER any successful add/delete so
        # downstream caches (e.g. HybridRetriever's BM25 index) can
        # invalidate. Fire-and-forget — exceptions are logged, not raised.
        self._on_change = on_change

    def _fire_on_change(self) -> None:
        if self._on_change is None:
            return
        try:
            self._on_change()
        except Exception:
            log.exception("on_change callback raised")

    async def ingest_file(self, *, filename: str, data: bytes) -> IngestResult:
        sha = hashlib.sha256(data).hexdigest()
        existing = await self.db.get_document_by_sha(sha)
        if existing:
            log.info("Skipping duplicate upload of %s (sha=%s…)", filename, sha[:8])
            return IngestResult(
                document_id=existing["id"],
                name=existing["name"],
                source_type=existing["source_type"],
                chunks=existing["chunk_count"],
                chars=existing["char_count"],
                duplicate=True,
            )

        text, source_type = load_bytes(filename, data)
        if not text:
            raise ValueError("File contains no extractable text")

        chunks = split_text(
            text,
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
        )
        if not chunks:
            raise ValueError("Text could not be split into chunks")

        # Persist the original bytes — useful for reprocessing if we change
        # chunk size or swap the embedder later.
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        safe_name = Path(filename).name.replace("/", "_")[:200]
        stored = self.upload_dir / f"{sha[:12]}__{safe_name}"
        stored.write_bytes(data)

        doc_id = await self.db.add_document(
            name=filename,
            source_type=source_type,
            chunk_count=len(chunks),
            char_count=len(text),
            file_path=str(stored),
            sha256=sha,
        )

        try:
            self.vector_store.add_chunks(
                document_id=doc_id,
                document_name=filename,
                chunks=chunks,
            )
        except Exception:
            # Roll the metadata row back so the UI never shows a "ready"
            # document that has zero searchable chunks.
            await self.db.delete_document(doc_id)
            raise

        log.info(
            "Ingested %s (%d chars → %d chunks, doc_id=%d)",
            filename,
            len(text),
            len(chunks),
            doc_id,
        )
        self._fire_on_change()
        return IngestResult(
            document_id=doc_id,
            name=filename,
            source_type=source_type,
            chunks=len(chunks),
            chars=len(text),
            duplicate=False,
        )

    async def delete(self, doc_id: int) -> bool:
        """Delete chunks first, then metadata. Order matters: if Chroma
        delete fails we'd rather leave the SQLite row pointing at a real
        chunk set than have orphan vectors with no name."""
        meta = await self.db.get_document(doc_id)
        if not meta:
            return False
        self.vector_store.delete_document(doc_id)
        await self.db.delete_document(doc_id)
        # Best-effort cleanup of the stored file.
        path = meta.get("file_path")
        if path:
            with contextlib.suppress(OSError):
                Path(path).unlink(missing_ok=True)
        self._fire_on_change()
        return True
