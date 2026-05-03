"""RAG pipeline (citation extraction)."""

from __future__ import annotations

from app.core.rag import RAGPipeline
from app.core.vectorstore import RetrievedChunk


def _chunks(n: int) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk_id=f"c{i}",
            document_id=i + 1,
            document_name=f"doc{i + 1}.md",
            text=f"Chunk {i + 1} text content.",
            score=1.0 - i * 0.1,
        )
        for i in range(n)
    ]


def test_extract_single_citation():
    cited = RAGPipeline._extract_citations("Answer goes here [2].", _chunks(3))
    assert [c.document_id for c in cited] == [2]


def test_extract_multiple_citations_in_order():
    cited = RAGPipeline._extract_citations(
        "Statement [3]. Another claim [1]. Detail [2].",
        _chunks(3),
    )
    # Order = order of first appearance in the answer.
    assert [c.document_id for c in cited] == [3, 1, 2]


def test_dedupe_repeated_citations():
    cited = RAGPipeline._extract_citations("[1] some [1] thing [1]", _chunks(3))
    assert [c.document_id for c in cited] == [1]


def test_out_of_range_citation_ignored():
    cited = RAGPipeline._extract_citations("Bogus [99].", _chunks(3))
    assert cited == []


def test_no_citations_falls_back_to_top_when_answer_substantive():
    long = "x" * 100
    cited = RAGPipeline._extract_citations(long, _chunks(3))
    assert len(cited) == 1
    assert cited[0].document_id == 1


def test_no_citations_no_fallback_when_answer_short():
    cited = RAGPipeline._extract_citations("ok", _chunks(3))
    assert cited == []


def test_empty_retrieved_returns_empty():
    assert RAGPipeline._extract_citations("Anything [1]", []) == []
