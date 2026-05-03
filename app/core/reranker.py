"""Optional re-ranking layer.

Re-ranking is the cheapest +20-30% retrieval-quality lift you can buy:
take the top-N candidates from hybrid search, send them through a
cross-encoder that sees question and chunk together, keep the best K.
The pool stays cheap (vector + BM25 are O(n)), and only K candidates
hit the slow re-ranker.

We support two backends:

  - `none`   — pass-through. Default; no extra deps, no API cost.
  - `cohere` — Cohere `rerank-multilingual-v3.0` via REST. ~$1/1M chars
    in, runs in ~200 ms for 16 candidates. Pluggable via `COHERE_API_KEY`.

Adding a third backend (e.g. local bge-reranker via ctransformers) is a
~30-line addition: implement `Reranker` and register it in `make_reranker`.
"""

from __future__ import annotations

import logging
from typing import Protocol

import httpx

from app.core.vectorstore import RetrievedChunk

log = logging.getLogger(__name__)


class Reranker(Protocol):
    async def rerank(
        self, query: str, candidates: list[RetrievedChunk], top_k: int
    ) -> list[RetrievedChunk]:
        ...


class _NoOpReranker:
    """Pass-through. Caller's existing ordering is preserved."""

    async def rerank(self, query: str, candidates: list[RetrievedChunk], top_k: int) -> list[RetrievedChunk]:
        return candidates[:top_k]


class _CohereReranker:
    """`rerank-multilingual-v3.0` — handles 100+ languages including Russian."""

    URL = "https://api.cohere.com/v1/rerank"
    MODEL = "rerank-multilingual-v3.0"
    TIMEOUT = 8.0

    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("COHERE_API_KEY is required for the Cohere reranker")
        self._api_key = api_key

    async def rerank(
        self, query: str, candidates: list[RetrievedChunk], top_k: int
    ) -> list[RetrievedChunk]:
        if not candidates:
            return []
        if len(candidates) <= 1:
            return candidates[:top_k]

        payload = {
            "model": self.MODEL,
            "query": query,
            "documents": [c.text for c in candidates],
            "top_n": min(top_k, len(candidates)),
        }
        try:
            async with httpx.AsyncClient(timeout=self.TIMEOUT) as client:
                resp = await client.post(
                    self.URL,
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            # Network blip / auth issue / Cohere down — degrade gracefully.
            # We still return the top-K from the original ranking so the user
            # gets an answer, just without re-ranking.
            log.warning("Cohere rerank failed (%s) — falling back to upstream order", e)
            return candidates[:top_k]

        # Cohere returns: {"results":[{"index":i,"relevance_score":s},...]}
        out: list[RetrievedChunk] = []
        out_of_range = 0
        for entry in data.get("results", []):
            i = int(entry.get("index", -1))
            score = float(entry.get("relevance_score", 0.0))
            if 0 <= i < len(candidates):
                src = candidates[i]
                out.append(
                    RetrievedChunk(
                        chunk_id=src.chunk_id,
                        document_id=src.document_id,
                        document_name=src.document_name,
                        text=src.text,
                        score=score,
                    )
                )
            else:
                out_of_range += 1
        if out_of_range:
            log.warning(
                "Cohere returned %d out-of-range indices (got %d valid)",
                out_of_range, len(out),
            )
        if not out:
            return candidates[:top_k]
        # If Cohere returned fewer items than asked for (truncation, partial
        # rate-limit), top up with the remaining candidates in their original
        # order so the caller still gets `top_k` items.
        if len(out) < top_k:
            seen = {c.chunk_id for c in out}
            for c in candidates:
                if c.chunk_id not in seen:
                    out.append(c)
                    if len(out) >= top_k:
                        break
        return out[:top_k]


def make_reranker(provider: str, *, cohere_api_key: str = "") -> Reranker:
    name = (provider or "none").lower().strip()
    if name in ("", "none", "off", "disabled"):
        return _NoOpReranker()
    if name == "cohere":
        return _CohereReranker(cohere_api_key)
    raise ValueError(
        f"Unknown RERANK_PROVIDER={provider!r}. Supported: none, cohere"
    )
