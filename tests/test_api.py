"""Public + admin API endpoints."""

from __future__ import annotations

import io


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] in ("ok", "degraded")
    assert body["chroma_collection"] == "knowledge_base"
    assert body["document_count"] == 0


def test_widget_config_is_public(client):
    res = client.get("/api/widget/config")
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["name"] == "Test Bot"
    assert "primary" in cfg["theme"]


def test_admin_requires_token(client):
    res = client.get("/api/admin/documents")
    assert res.status_code == 401


def test_admin_rejects_wrong_token(client):
    res = client.get("/api/admin/documents", headers={"Authorization": "Bearer wrong"})
    assert res.status_code == 401


def test_admin_lists_empty_kb(client, admin_headers):
    res = client.get("/api/admin/documents", headers=admin_headers)
    assert res.status_code == 200
    body = res.json()
    assert body["documents"] == []
    assert body["total_chunks"] == 0


def test_upload_markdown_indexes_and_lists(client, admin_headers):
    md = b"# Pricing\n\nNDA review costs four hundred dollars. SaaS terms start at $1,800.\n" * 3
    res = client.post(
        "/api/admin/documents",
        headers=admin_headers,
        files={"file": ("pricing.md", io.BytesIO(md), "text/markdown")},
    )
    assert res.status_code == 201
    doc = res.json()
    assert doc["name"] == "pricing.md"
    assert doc["chunk_count"] >= 1
    assert doc["source_type"] == "markdown"

    listing = client.get("/api/admin/documents", headers=admin_headers).json()
    assert len(listing["documents"]) == 1
    assert listing["total_chunks"] == doc["chunk_count"]


def test_upload_unsupported_format_returns_415(client, admin_headers):
    res = client.post(
        "/api/admin/documents",
        headers=admin_headers,
        files={"file": ("bad.png", io.BytesIO(b"\x89PNG"), "image/png")},
    )
    assert res.status_code == 415


def test_delete_document(client, admin_headers):
    md = b"# Hello\n\nSome content. " * 30
    upload = client.post(
        "/api/admin/documents",
        headers=admin_headers,
        files={"file": ("h.md", io.BytesIO(md), "text/markdown")},
    ).json()
    res = client.delete(f"/api/admin/documents/{upload['id']}", headers=admin_headers)
    assert res.status_code == 204
    again = client.delete(f"/api/admin/documents/{upload['id']}", headers=admin_headers)
    assert again.status_code == 404


def test_chat_returns_answer_with_session(client, admin_headers):
    md = (
        b"# Hotel\n\nBreakfast is served from 07:00 to 10:30.\n"
        b"Check-in is from 15:00. Check-out by 11:00.\n"
    ) * 5
    client.post(
        "/api/admin/documents",
        headers=admin_headers,
        files={"file": ("hotel.md", io.BytesIO(md), "text/markdown")},
    )

    res = client.post(
        "/api/chat",
        json={"message": "What time is breakfast?", "history": [], "session_id": None},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["answer"]
    assert isinstance(body["session_id"], str) and len(body["session_id"]) >= 16
    assert body["used_documents"] >= 1
    assert isinstance(body["citations"], list)


def test_chat_with_continuing_session(client, admin_headers):
    md = b"# Pricing\n\nThe initial consultation costs $250 for 45 minutes.\n" * 5
    client.post(
        "/api/admin/documents",
        headers=admin_headers,
        files={"file": ("p.md", io.BytesIO(md), "text/markdown")},
    )
    first = client.post(
        "/api/chat",
        json={"message": "How much is a consultation?", "history": []},
    ).json()
    sid = first["session_id"]

    second = client.post(
        "/api/chat",
        json={
            "message": "And how long is it?",
            "history": [
                {"role": "user", "content": "How much is a consultation?"},
                {"role": "assistant", "content": first["answer"]},
            ],
            "session_id": sid,
        },
    ).json()
    assert second["session_id"] == sid


def test_chat_validates_message_length(client):
    res = client.post("/api/chat", json={"message": "", "history": []})
    assert res.status_code == 422


def test_cors_headers_set(client):
    res = client.options(
        "/api/chat",
        headers={
            "Origin": "https://acme.com",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    # Should be 200/204 with CORS headers — never 405.
    assert res.status_code in (200, 204)
    assert "access-control-allow-origin" in {k.lower() for k in res.headers}
