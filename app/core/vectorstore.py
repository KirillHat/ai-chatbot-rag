"""ChromaDB wrapper.

Chroma is embedded (no external server) and ships with a default
ONNX MiniLM-L6-v2 embedding function — fine for English KBs up to a few
thousand chunks. Swap the embedding function for OpenAI / Voyage / Cohere
in `_embedding_function` without touching the rest of the codebase.
"""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

log = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_base"

# `paraphrase-multilingual-MiniLM-L12-v2` covers 50+ languages including
# Russian / Spanish / German / French / Chinese — drop-in for English KBs
# that need to handle multilingual queries. Slightly bigger than the default
# (~120 MB cold start vs ~25 MB) but still CPU-friendly.
_MULTILINGUAL_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: int
    document_name: str
    text: str
    score: float  # 1.0 = perfect match, 0.0 = unrelated (cosine-similarity scaled)


def _embedding_function(model_name: str = "default"):
    """Pick an embedding function from `EMBEDDING_MODEL`.

    - `default`  → bundled ONNX MiniLM-L6-v2 (English-only, ships with chromadb)
    - `multilingual` → sentence-transformers paraphrase-multilingual-MiniLM-L12-v2
    - `none`     → no embeddings (BM25-only mode, used by some tests)
    - any other value is treated as a sentence-transformers model id
    """
    name = (model_name or "default").lower().strip()
    if name in ("none", "off", "disabled"):
        return None
    if name == "default":
        return embedding_functions.DefaultEmbeddingFunction()
    st_model = _MULTILINGUAL_MODEL if name == "multilingual" else model_name
    try:
        return embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=st_model
        )
    except (ImportError, ValueError) as e:
        # Chroma may raise ValueError("The sentence_transformers python
        # package is not installed") OR a real ImportError, depending on
        # the chroma version. Catch both and surface a clear hint instead
        # of the cryptic upstream message.
        raise RuntimeError(
            f"EMBEDDING_MODEL={model_name!r} requires `sentence-transformers`. "
            "Install with `pip install sentence-transformers` and restart."
        ) from e


class VectorStore:
    """Persistent Chroma collection for RAG retrieval."""

    def __init__(self, persist_dir: Path, embedding_model: str = "default"):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model = embedding_model
        self._client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False, allow_reset=True),
        )
        ef = _embedding_function(embedding_model)
        if ef is None:
            # BM25-only mode: still create a collection so we can store text,
            # but with a no-op embedding fn that never gets called for query.
            ef = embedding_functions.DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )

    @property
    def collection_name(self) -> str:
        return COLLECTION_NAME

    def count(self) -> int:
        return self._collection.count()

    def add_chunks(
        self,
        *,
        document_id: int,
        document_name: str,
        chunks: list[str],
    ) -> list[str]:
        """Add chunks for a document. Returns the chunk ids written to Chroma."""
        if not chunks:
            return []
        ids = [f"doc{document_id}-{i}" for i in range(len(chunks))]
        metadatas: list[dict[str, Any]] = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]
        self._collection.add(ids=ids, documents=chunks, metadatas=metadatas)
        return ids

    def delete_document(self, document_id: int) -> int:
        """Delete every chunk belonging to one document. Returns count deleted."""
        existing = self._collection.get(where={"document_id": document_id})
        ids = existing.get("ids") or []
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    def query(self, query_text: str, top_k: int) -> list[RetrievedChunk]:
        if not query_text.strip():
            return []
        try:
            res = self._collection.query(
                query_texts=[query_text],
                n_results=min(top_k, max(self.count(), 1)),
            )
        except Exception as e:
            log.warning("Chroma query failed: %s", e)
            return []

        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        # `distances` for cosine space is in [0, 2]; convert to a [0, 1] similarity score.
        dists = (res.get("distances") or [[]])[0]

        out: list[RetrievedChunk] = []
        for cid, text, meta, dist in zip(ids, docs, metas, dists, strict=False):
            score = max(0.0, 1.0 - float(dist) / 2.0)
            out.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=int((meta or {}).get("document_id", 0)),
                    document_name=str((meta or {}).get("document_name", "")),
                    text=text or "",
                    score=score,
                )
            )
        return out

    def all_chunks(self) -> list[RetrievedChunk]:
        """Dump every chunk for BM25 indexing.

        Cheap because Chroma keeps all docs in a single SQLite file and
        we only need text + metadata, not vectors. Reads are O(N).
        """
        try:
            res = self._collection.get(include=["documents", "metadatas"])
        except Exception as e:
            log.warning("Chroma full-dump failed: %s", e)
            return []
        ids = res.get("ids") or []
        docs = res.get("documents") or []
        metas = res.get("metadatas") or []
        out: list[RetrievedChunk] = []
        for cid, text, meta in zip(ids, docs, metas, strict=False):
            out.append(
                RetrievedChunk(
                    chunk_id=cid,
                    document_id=int((meta or {}).get("document_id", 0)),
                    document_name=str((meta or {}).get("document_name", "")),
                    text=text or "",
                    score=0.0,  # caller assigns
                )
            )
        return out

    def reset(self) -> None:
        """Drop and recreate the collection. Used by tests."""
        with contextlib.suppress(Exception):
            self._client.delete_collection(COLLECTION_NAME)
        ef = _embedding_function(self.embedding_model) or embedding_functions.DefaultEmbeddingFunction()
        self._collection = self._client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
            metadata={"hnsw:space": "cosine"},
        )
