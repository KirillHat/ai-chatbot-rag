"""RAG pipeline glue.

`RAGPipeline` owns the full retrieve → re-rank → generate path:

  1. **Hybrid retrieve** (BM25 + vector via RRF) → `pool_size` candidates
  2. **Optional re-rank** (Cohere by default off) → keep top-K
  3. **Claude completion** with the top-K chunks as numbered context
  4. **Citation extraction** — parse `[n]` markers back into source docs
"""

from __future__ import annotations

import re

from app.core.claude import ClaudeClient, render_context
from app.core.reranker import Reranker
from app.core.retrieval import HybridRetriever
from app.core.vectorstore import RetrievedChunk

CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class RAGPipeline:
    def __init__(
        self,
        retriever: HybridRetriever,
        claude: ClaudeClient,
        top_k: int,
        reranker: Reranker | None = None,
        pool_size: int | None = None,
    ):
        self.retriever = retriever
        self.claude = claude
        self.top_k = top_k
        self.reranker = reranker
        # If a reranker is wired up we pull a wider pool so it has something
        # to filter; otherwise we just retrieve top_k directly.
        self.pool_size = pool_size if pool_size is not None else (
            max(top_k * 4, 12) if reranker else top_k
        )

    @property
    def vector_store(self):
        """Back-compat shim — older callers expect `pipeline.vector_store`."""
        return self.retriever.vector_store

    async def answer(
        self,
        *,
        question: str,
        history: list[dict],
    ) -> tuple[str, list[RetrievedChunk], list[RetrievedChunk]]:
        """Run retrieve → (rerank) → generate.

        Returns (answer_text, all_retrieved_chunks, cited_chunks). Cited
        chunks are the subset that actually appear in the answer's [n]
        markers (with a fallback to the top retrieved chunk when the model
        forgot to cite).
        """
        pool = self.retriever.retrieve(question, top_k=self.pool_size)
        if self.reranker and len(pool) > 1:
            retrieved = await self.reranker.rerank(question, pool, self.top_k)
        else:
            retrieved = pool[: self.top_k]
        context = render_context(retrieved)
        result = await self.claude.complete(
            user_message=question,
            history=history,
            context_block=context,
        )
        cited = self._extract_citations(result.text, retrieved)
        return result.text, retrieved, cited

    @staticmethod
    def _extract_citations(
        answer: str,
        retrieved: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Pick out the chunks the model actually cited.

        Falls back to the top retrieved chunk if the model forgot citations
        but the answer is non-trivial — better to show *some* source than
        none, since the user expects citations.
        """
        if not retrieved:
            return []
        seen: set[int] = set()
        ordered: list[RetrievedChunk] = []
        for match in CITATION_PATTERN.finditer(answer):
            idx = int(match.group(1)) - 1
            if 0 <= idx < len(retrieved) and idx not in seen:
                seen.add(idx)
                ordered.append(retrieved[idx])
        if not ordered and len(answer) > 60:
            ordered = retrieved[:1]
        return ordered
