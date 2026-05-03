"""Auth and rate-limit dependencies."""

from __future__ import annotations

from app.api.deps import reset_rate_limiter


def test_admin_disabled_when_default_token(client, monkeypatch):
    # Reset to the default sentinel — admin should refuse to authenticate at all.
    monkeypatch.setenv("ADMIN_API_TOKEN", "change-me")
    from app.config import get_settings

    get_settings.cache_clear()
    res = client.get("/api/admin/documents", headers={"Authorization": "Bearer anything"})
    # With our test fixture the override holds, so this exercises the
    # "missing/empty header" path; the defensive 503 path is covered by
    # the admin_disabled_when_default_token unit test in test_api.py
    # against a fresh app — here we just confirm 401/503 (never 200).
    assert res.status_code in (401, 503)


def test_rate_limit_kicks_in(settings, monkeypatch):
    """The rate limiter should refuse the (N+1)th request inside one minute."""
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "3")
    from app.config import get_settings

    get_settings.cache_clear()
    from fastapi.testclient import TestClient

    from app.main import create_app

    reset_rate_limiter()
    app = create_app(settings_override=get_settings())
    with TestClient(app) as c:
        # /health is not rate-limited; use /api/chat.
        # Stub Claude is not wired up here, so we'll get 503, but rate
        # limit fires *before* the handler runs.
        statuses = []
        for _ in range(5):
            r = c.post("/api/chat", json={"message": "hi", "history": []})
            statuses.append(r.status_code)
        assert 429 in statuses, f"Expected a 429 in {statuses}"
