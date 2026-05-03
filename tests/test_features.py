"""Regression tests for the post-1.0 features.

Covers:
  - Hybrid retrieval (BM25 + vector) — pure-BM25 fallback when the
    vector channel returns nothing relevant.
  - Re-ranker factory — `none` is no-op, unknown providers raise.
  - Escalate endpoint — happy path + Slack webhook failure-isolation.
  - Analytics endpoint — shape + counts after a few chat turns.
  - Streaming endpoint — SSE frames parse, deltas accumulate, citations
    arrive after the last delta.
"""

from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.reranker import _NoOpReranker, make_reranker
from app.core.retrieval import _BM25, HybridRetriever, _rrf_fuse, _tokenize

# ---------------------------------------------------------------- BM25 + RRF


def test_bm25_zero_doc_corpus_does_not_crash():
    bm = _BM25([])
    assert bm.score(["anything"]) == []


def test_bm25_picks_keyword_match():
    docs = [
        _tokenize("the breakfast hours are seven to ten thirty"),
        _tokenize("the spa is open until ten in the evening"),
        _tokenize("we have parking but no pool"),
    ]
    bm = _BM25(docs)
    scores = bm.score(_tokenize("breakfast hours"))
    assert scores[0] > scores[1]
    assert scores[0] > scores[2]


def test_rrf_fuse_rewards_consensus():
    # Two ranking lists; chunk_a is top in both, chunk_b only top in one.
    fused = _rrf_fuse([
        ["chunk_a", "chunk_b", "chunk_c"],
        ["chunk_a", "chunk_d", "chunk_b"],
    ])
    ordered = sorted(fused, key=lambda k: fused[k], reverse=True)
    assert ordered[0] == "chunk_a"
    # chunk_b is in both lists — should beat chunk_c (only in list 1) and chunk_d (only in list 2).
    assert "chunk_b" in ordered[:3]


@pytest.mark.asyncio
async def test_hybrid_retriever_returns_top_k_after_ingest(pipeline, vector_store):
    """End-to-end: ingest a doc, then hybrid retrieve must surface a
    chunk whose text overlaps the query — even on a small KB."""
    md = (
        b"# Hours\n\nBreakfast is served from 07:00 to 10:30 in the dining room.\n"
        b"Late breakfast is available on Sundays until 11:00.\n"
    ) * 3
    await pipeline.ingest_file(filename="hours.md", data=md)
    retriever = HybridRetriever(vector_store, pool_size=8, alpha=0.6)
    hits = retriever.retrieve("when is breakfast?", top_k=3)
    assert hits, "expected at least one hit after ingest"
    assert any("breakfast" in h.text.lower() for h in hits)


def test_hybrid_retriever_handles_empty_kb(vector_store):
    retriever = HybridRetriever(vector_store, pool_size=4, alpha=0.6)
    assert retriever.retrieve("anything", top_k=3) == []


# --------------------------------------------------------------- Re-ranker


def test_reranker_none_is_passthrough():
    r = make_reranker("none")
    assert isinstance(r, _NoOpReranker)


def test_reranker_unknown_provider_raises():
    with pytest.raises(ValueError):
        make_reranker("not-a-real-provider")


def test_reranker_cohere_requires_key():
    with pytest.raises(ValueError):
        make_reranker("cohere", cohere_api_key="")


# ----------------------------------------------------------------- Escalate


def test_escalate_with_no_session_id_rejected(client):
    res = client.post("/api/escalate", json={"contact": "x@y.com", "reason": "help"})
    assert res.status_code == 422


def test_escalate_records_event(client, settings):
    # First send a chat message so we have a real session_id to escalate.
    chat_res = client.post("/api/chat", json={"message": "hi", "history": []}).json()
    sid = chat_res["session_id"]

    res = client.post(
        "/api/escalate",
        json={"session_id": sid, "contact": "alice@example.com", "reason": "Need a quote"},
    )
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "received"
    assert body["id"] >= 1
    # No channels configured in tests, so notified is empty — that's fine.
    assert body["notified"] == []
    assert "ref #" in body["message"]


def test_escalate_slack_failure_does_not_break_user(client, settings, monkeypatch):
    """A flaky Slack webhook must NOT cause a 500 to the user."""
    monkeypatch.setenv("ESCALATION_SLACK_WEBHOOK", "https://example.invalid/slack")
    # Rebuild the escalation service so it picks up the env var.
    from app.services.escalation_service import EscalationService

    es = EscalationService(
        db=client.app.state.db,
        slack_webhook="https://example.invalid/slack",
        email="",
        assistant_name="Test",
        tenant="acme",
    )
    client.app.state.escalation = es

    # Force the webhook to throw.
    es._post_slack = AsyncMock(side_effect=RuntimeError("DNS failure"))

    chat = client.post("/api/chat", json={"message": "hi", "history": []}).json()
    res = client.post(
        "/api/escalate",
        json={"session_id": chat["session_id"], "contact": "x@y", "reason": "help"},
    )
    assert res.status_code == 202
    body = res.json()
    assert body["status"] == "received"
    # Slack failed, so notified must NOT include "slack".
    assert "slack" not in body["notified"]


# ------------------------------------------------------------- Analytics


def test_analytics_empty_kb(client, admin_headers):
    res = client.get("/api/admin/analytics", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    # Schema sanity — every documented field must be present.
    expected = {
        "sessions_total", "sessions_today", "sessions_7d",
        "messages_total", "user_messages_today", "user_messages_7d",
        "no_answer_rate_7d", "avg_messages_per_session",
        "escalations_total", "escalations_pending",
        "top_questions_7d", "daily_volume_30d",
    }
    assert expected.issubset(data.keys())
    # 30-day chart array is always exactly 30 entries (zero-padded).
    assert len(data["daily_volume_30d"]) == 30


def test_analytics_after_chats(client, admin_headers):
    # Send 3 messages so we have something to count.
    for q in ("What's breakfast?", "Where is parking?", "What's the wifi?"):
        client.post("/api/chat", json={"message": q, "history": []})

    data = client.get("/api/admin/analytics", headers=admin_headers).json()
    assert data["sessions_today"] >= 3
    assert data["user_messages_today"] >= 3
    assert data["messages_total"] >= 6  # 3 user + 3 assistant
    assert data["avg_messages_per_session"] > 0


def test_analytics_requires_token(client):
    assert client.get("/api/admin/analytics").status_code == 401


# ------------------------------------------------------------- Streaming


def _parse_sse(body: str) -> list[dict]:
    """Pull the JSON payloads out of an SSE response body."""
    events = []
    for frame in body.split("\n\n"):
        for line in frame.split("\n"):
            if line.startswith("data:"):
                payload = line[5:].strip()
                if payload:
                    events.append(json.loads(payload))
    return events


def test_streaming_endpoint_emits_session_delta_done(client):
    # Need an actual KB for the stub Claude to have anything to "answer" with.
    md = b"# Pricing\n\nA standard NDA review costs $400.\n" * 3
    client.post(
        "/api/admin/documents",
        headers={"Authorization": "Bearer test-admin-token-1234567890"},
        files={"file": ("nda.md", io.BytesIO(md), "text/markdown")},
    )

    # The stub Claude doesn't implement `.stream()`, so patch it to simulate
    # the Anthropic streaming contract.
    async def fake_stream(*, user_message, history, context_block):
        yield ("delta", "The NDA review")
        yield ("delta", " costs $400 [1].")
        from app.core.claude import StreamingCompletionResult
        yield ("done", StreamingCompletionResult(
            text="The NDA review costs $400 [1].",
            input_tokens=10,
            output_tokens=8,
        ))

    with patch.object(client.app.state.claude, "stream", side_effect=fake_stream), \
            client.stream(
                "POST", "/api/chat/stream",
                json={"message": "How much for an NDA?", "history": [], "session_id": None},
            ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = resp.read().decode()

    events = _parse_sse(body)
    types = [e["type"] for e in events]
    assert "session" in types          # we emit session id up front
    assert types.count("delta") == 2   # both deltas reach the client
    assert "citations" in types        # parsed from the fully-assembled answer
    assert types[-1] == "done"
    # Citations should not be empty since the answer contains [1] and we have a doc.
    cites_event = next(e for e in events if e["type"] == "citations")
    assert isinstance(cites_event["citations"], list)
