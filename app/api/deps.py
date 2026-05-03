"""FastAPI dependency providers.

Singletons live on `app.state` so we can swap them in tests via
`app.state.<name> = mock_thing` instead of monkey-patching modules.
"""

from __future__ import annotations

import secrets
import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status

from app.config import Settings, get_settings
from app.core.rag import RAGPipeline
from app.db.database import Database
from app.ingestion.pipeline import IngestionPipeline
from app.services.chat_service import ChatService

SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_db(request: Request) -> Database:
    return request.app.state.db


def get_rag(request: Request) -> RAGPipeline:
    return request.app.state.rag


def get_ingestion(request: Request) -> IngestionPipeline:
    return request.app.state.ingestion


def get_chat(request: Request) -> ChatService:
    return request.app.state.chat


def require_admin(
    settings: SettingsDep,
    authorization: Annotated[str | None, Header()] = None,
) -> None:
    """Bearer-token guard for admin endpoints.

    Constant-time comparison protects against trivial timing oracles.
    A blank `ADMIN_API_TOKEN` is treated as "admin disabled" — return 503
    rather than letting an attacker brute-force a default value.
    """
    if not settings.admin_api_token or settings.admin_api_token == "change-me":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API is disabled — set ADMIN_API_TOKEN in .env",
        )
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if not secrets.compare_digest(token, settings.admin_api_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# --- Per-IP sliding-window rate limiter (in-process, fine for one replica) ---

_REQS: dict[str, deque[float]] = defaultdict(deque)
# Sweep cadence for evicting stale IP entries. Without this, a scanner
# hitting /api/chat with random IPs leaks memory unboundedly.
_LAST_SWEEP: float = 0.0
_SWEEP_INTERVAL = 300.0  # seconds


def _sweep_stale(now: float, window: float) -> None:
    """Remove entries whose most-recent request is older than `window`."""
    global _LAST_SWEEP
    if now - _LAST_SWEEP < _SWEEP_INTERVAL:
        return
    _LAST_SWEEP = now
    # Materialise the keys first — we mutate the dict during iteration.
    stale = [
        ip for ip, bucket in _REQS.items()
        if not bucket or now - bucket[-1] > window
    ]
    for ip in stale:
        _REQS.pop(ip, None)


def rate_limit(settings: SettingsDep, request: Request) -> None:
    ip = (request.client.host if request.client else None) or "unknown"
    now = time.monotonic()
    window = 60.0
    _sweep_stale(now, window)
    bucket = _REQS[ip]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= settings.rate_limit_per_minute:
        retry_after = max(1, int(window - (now - bucket[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many requests — try again in {retry_after}s",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def reset_rate_limiter() -> None:
    """Test helper — clears the in-memory bucket between tests."""
    global _LAST_SWEEP
    _REQS.clear()
    _ESCALATE_REQS.clear()
    _LAST_SWEEP = 0.0


# Separate, much smaller bucket for /api/escalate. We don't want a chatty
# user to be unable to request a human just because they hit /api/chat too
# many times — different intent, different envelope. Hard-coded at 5/min;
# the chat path is the one that needs to be configurable.
_ESCALATE_REQS: dict[str, deque[float]] = defaultdict(deque)
_ESCALATE_PER_MIN = 5


def rate_limit_escalate(request: Request) -> None:
    ip = (request.client.host if request.client else None) or "unknown"
    now = time.monotonic()
    window = 60.0
    bucket = _ESCALATE_REQS[ip]
    while bucket and now - bucket[0] > window:
        bucket.popleft()
    if len(bucket) >= _ESCALATE_PER_MIN:
        retry_after = max(1, int(window - (now - bucket[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many escalation requests — try again in {retry_after}s",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)
