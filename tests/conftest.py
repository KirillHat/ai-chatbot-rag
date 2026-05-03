"""Shared pytest fixtures.

Tests run against a fresh temporary SQLite + Chroma + filesystem on every
session — never the real `data/` directory. The Anthropic client is
replaced with a stub so we never make a network call.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.api.deps import reset_rate_limiter
from app.config import Settings, get_settings
from app.core.claude import ClaudeClient, CompletionResult
from app.core.rag import RAGPipeline
from app.core.retrieval import HybridRetriever
from app.core.vectorstore import VectorStore
from app.db.database import Database
from app.ingestion.pipeline import IngestionPipeline
from app.main import create_app
from app.services.chat_service import ChatService


class StubClaude(ClaudeClient):
    """Replaces network calls with a deterministic in-process implementation."""

    def __init__(self):
        super().__init__(
            api_key="test-key",  # any non-empty value flips `configured` on
            model="stub",
            max_tokens=256,
            assistant_name="Test Bot",
            company="acme",
        )
        self._client = object()  # truthy → `configured` is True
        self.calls: list[dict[str, Any]] = []
        self.canned_answer: str | None = None

    async def complete(self, *, user_message, history, context_block):
        self.calls.append({
            "user_message": user_message,
            "history": history,
            "context_block": context_block,
        })
        text = self.canned_answer or (
            f"This is a test answer about: {user_message[:80]}. "
            f"Based on the knowledge base [1]."
        )
        return CompletionResult(text=text, input_tokens=10, output_tokens=20)


@pytest.fixture
def settings(tmp_path: Path, monkeypatch) -> Settings:
    monkeypatch.setenv("ADMIN_API_TOKEN", "test-admin-token-1234567890")
    monkeypatch.setenv("CHROMA_DIR", str(tmp_path / "chroma"))
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "app.db"))
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setenv("RATE_LIMIT_PER_MINUTE", "600")
    monkeypatch.setenv("ASSISTANT_NAME", "Test Bot")
    monkeypatch.setenv("ASSISTANT_TENANT", "acme")
    monkeypatch.setenv("CHUNK_SIZE", "400")
    monkeypatch.setenv("CHUNK_OVERLAP", "50")
    monkeypatch.setenv("TOP_K", "3")
    monkeypatch.setenv("CORS_ORIGINS", "*")
    # ANTHROPIC_API_KEY left unset on purpose; StubClaude overrides it.
    get_settings.cache_clear()
    s = Settings()
    s.ensure_dirs()
    return s


@pytest.fixture
def stub_claude() -> StubClaude:
    return StubClaude()


@pytest.fixture
def client(settings: Settings, stub_claude: StubClaude) -> TestClient:
    """A configured FastAPI TestClient with a stub Claude wired in."""
    reset_rate_limiter()
    app = create_app(settings_override=settings)

    # Replace lifespan singletons with our stub Claude. We still need to run
    # the lifespan once so the DB tables get created.
    with TestClient(app) as c:
        app.state.claude = stub_claude
        retriever = HybridRetriever(
            app.state.vector_store,
            pool_size=settings.retrieval_pool,
            alpha=settings.hybrid_alpha,
        )
        app.state.rag = RAGPipeline(
            retriever=retriever,
            claude=stub_claude,
            top_k=settings.top_k,
        )
        app.state.chat = ChatService(rag=app.state.rag, db=app.state.db)
        yield c


@pytest.fixture
def admin_headers(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.admin_api_token}"}


@pytest.fixture
async def db(settings: Settings) -> Database:
    d = Database(settings.sqlite_path)
    await d.init()
    return d


@pytest.fixture
def vector_store(settings: Settings) -> VectorStore:
    vs = VectorStore(settings.chroma_dir)
    vs.reset()
    return vs


@pytest.fixture
async def pipeline(settings: Settings, db: Database, vector_store: VectorStore) -> IngestionPipeline:
    return IngestionPipeline(
        db=db,
        vector_store=vector_store,
        upload_dir=settings.upload_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
