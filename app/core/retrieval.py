"""Hybrid retrieval: BM25 lexical + Chroma semantic, fused via RRF.

Why hybrid:
    Pure vector retrieval is great at "what time is breakfast" → "Breakfast
    is served from 07:00–10:30" (no shared tokens). It's bad at
    "What is policy SOC 2?" → SOC 2 is the literal token; semantic similarity
    glides right past unless the embedding model has seen "SOC 2" a lot.
    BM25 catches keyword hits like that. Reciprocal Rank Fusion (RRF) merges
    the two ranked lists in a way that doesn't require score normalization —
    it only cares about position. Robust to one channel returning weird
    scores while the other behaves.

Cost:
    BM25 rebuilds an in-memory index on every query from
    `vector_store.all_chunks()`. Fine up to ~10k chunks (which is already a
    big KB — one big book of legal precedents, or ~500 hotel-FAQ-sized
    pages). For larger KBs, swap this for a persistent BM25 (e.g. tantivy
    or pgsql tsvector). The seam is `_BM25.score()`.
"""

from __future__ import annotations

import logging
import math
import re
from collections import Counter
from collections.abc import Iterable

from app.core.vectorstore import RetrievedChunk, VectorStore

log = logging.getLogger(__name__)

# Reasonable defaults from the BM25Plus paper; the only case worth tuning
# is when chunks are very short (< ~100 tokens) — drop b to ~0.5.
_K1 = 1.5
_B = 0.75
_RRF_K = 60  # standard constant from the original RRF paper


def _tokenize(text: str) -> list[str]:
    """Lowercase + split on non-word. Cheap, language-agnostic for the few
    languages we care about (English / Russian / Spanish / German all
    accept this fallback). Replace with a real tokenizer if you need
    proper CJK or stemming."""
    return re.findall(r"\w+", (text or "").lower())


class _BM25:
    """Stateless one-shot BM25 over an in-memory corpus."""

    def __init__(self, docs: list[list[str]]):
        self.docs = docs
        self.n = len(docs)
        self.doc_lens = [len(d) for d in docs]
        self.avg_len = (sum(self.doc_lens) / self.n) if self.n else 0.0
        self.doc_freqs: list[Counter[str]] = [Counter(d) for d in docs]
        df: Counter[str] = Counter()
        for tf in self.doc_freqs:
            df.update(tf.keys())
        # Smoothed IDF; the +1 in numerator keeps it non-negative.
        self.idf = {
            term: math.log((self.n - freq + 0.5) / (freq + 0.5) + 1.0)
            for term, freq in df.items()
        }

    def score(self, query: list[str]) -> list[float]:
        scores = [0.0] * self.n
        if self.avg_len == 0.0:
            return scores
        for term in query:
            idf = self.idf.get(term)
            if idf is None:
                continue
            for i, tf in enumerate(self.doc_freqs):
                freq = tf.get(term, 0)
                if freq == 0:
                    continue
                norm = 1.0 - _B + _B * (self.doc_lens[i] / self.avg_len)
                scores[i] += idf * (freq * (_K1 + 1)) / (freq + _K1 * norm)
        return scores


def _rrf_fuse(rank_lists: Iterable[list[str]], k: int = _RRF_K) -> dict[str, float]:
    """Reciprocal Rank Fusion. Each rank list is a list of chunk ids in
    ranked order (best first); we sum 1/(k + rank) across lists per id.
    Higher fused score = better."""
    fused: dict[str, float] = {}
    for ranking in rank_lists:
        for rank, chunk_id in enumerate(ranking):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank + 1)
    return fused


class HybridRetriever:
    """RRF over BM25 + vector. The BM25 index is rebuilt on demand from the
    vector store and cached until the chunk count changes — so a steady
    stream of queries on a stable KB is O(query) per request, not O(N)."""

    def __init__(
        self,
        vector_store: VectorStore,
        *,
        pool_size: int,
        alpha: float = 0.6,
    ):
        self.vector_store = vector_store
        self.pool_size = pool_size
        # `alpha` weights the vector ranking when fusing. We implement it by
        # duplicating the vector ranking `weight_v` times in the RRF input —
        # cheap proxy for a weighted RRF.
        self.alpha = max(0.0, min(1.0, alpha))
        # Cached state: BM25 index, the chunks it was built from, and the
        # vector-store count we observed at build time. We invalidate on
        # count change OR explicit invalidate() (called from ingestion +
        # delete to handle re-uploads of the same N chunks).
        self._bm25: _BM25 | None = None
        self._cached_chunks: list[RetrievedChunk] = []
        self._cached_count: int = -1

    def invalidate(self) -> None:
        """Drop the cached BM25 index — call after ingest / delete."""
        self._bm25 = None
        self._cached_chunks = []
        self._cached_count = -1

    def _ensure_bm25(self) -> tuple[_BM25 | None, list[RetrievedChunk]]:
        current = self.vector_store.count()
        if self._bm25 is not None and current == self._cached_count:
            return self._bm25, self._cached_chunks
        chunks = self.vector_store.all_chunks()
        if not chunks:
            self._bm25 = None
            self._cached_chunks = []
            self._cached_count = current
            return None, []
        self._bm25 = _BM25([_tokenize(c.text) for c in chunks])
        self._cached_chunks = chunks
        self._cached_count = current
        log.debug("BM25 index rebuilt (%d chunks)", len(chunks))
        return self._bm25, chunks

    def retrieve(self, query: str, top_k: int) -> list[RetrievedChunk]:
        if not query.strip():
            return []
        # 1) Lexical channel — use the cached index if the corpus hasn't grown.
        bm25, all_chunks = self._ensure_bm25()
        if bm25 is None:
            return []
        bm_scores = bm25.score(_tokenize(query))
        bm_ranked = [
            c.chunk_id for _, c in sorted(
                zip(bm_scores, all_chunks, strict=False),
                key=lambda x: x[0],
                reverse=True,
            )[: self.pool_size]
            if _ > 0  # skip zero-score (no token overlap)
        ]
        # 2) Vector channel
        vec_hits = self.vector_store.query(query, top_k=self.pool_size)
        vec_ranked = [c.chunk_id for c in vec_hits]
        # 3) Fuse — duplicate the heavier channel proportional to alpha.
        # alpha = 0.6 → vector counted ceil(6) times, BM25 ceil(4) times.
        v_weight = max(1, round(self.alpha * 10))
        b_weight = max(1, round((1 - self.alpha) * 10))
        rank_lists = [vec_ranked] * v_weight + [bm_ranked] * b_weight
        fused = _rrf_fuse(rank_lists)
        # 4) Resolve top-k chunk ids back to RetrievedChunk objects, picking
        # the richer source (vector hits already carry similarity scores).
        by_id: dict[str, RetrievedChunk] = {c.chunk_id: c for c in all_chunks}
        for c in vec_hits:
            by_id[c.chunk_id] = c  # prefer vector entry — has cosine score
        ordered_ids = sorted(fused.keys(), key=lambda i: fused[i], reverse=True)[:top_k]
        out: list[RetrievedChunk] = []
        for cid in ordered_ids:
            c = by_id.get(cid)
            if c is None:
                continue
            # If the chunk only made it via BM25, synthesize a score from
            # its fused rank so downstream UI doesn't show 0.0.
            score = c.score if c.score > 0 else min(1.0, fused[cid] * 10)
            out.append(
                RetrievedChunk(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    document_name=c.document_name,
                    text=c.text,
                    score=score,
                )
            )
        log.debug(
            "Hybrid retrieve: query=%r vec_hits=%d bm_hits=%d fused→%d",
            query[:60], len(vec_hits), len(bm_ranked), len(out),
        )
        return out
