"""FastAPI application factory.

`create_app()` wires the singletons (DB, vector store, RAG) and mounts
the routes. Tests build their own app via `create_app(settings_override=…)`
so they never touch the production DB or hit Anthropic.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import admin, chat, escalate, health, widget
from app.config import Settings, get_settings
from app.core.claude import ClaudeClient
from app.core.rag import RAGPipeline
from app.core.reranker import make_reranker
from app.core.retrieval import HybridRetriever
from app.core.vectorstore import VectorStore
from app.db.database import Database
from app.ingestion.pipeline import IngestionPipeline
from app.observability import REQUEST_ID_CTX, MetricsStore, install_request_id_filter
from app.services.chat_service import ChatService
from app.services.escalation_service import EscalationService

log = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s [req=%(request_id)s] %(name)s: %(message)s",
)
install_request_id_filter()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = app.state.settings
    db = Database(settings.sqlite_path)
    await db.init()
    # Same fail-soft policy as the reranker: a misconfigured embedding
    # model shouldn't take the whole server down.
    try:
        vector_store = VectorStore(
            settings.chroma_dir, embedding_model=settings.embedding_model
        )
    except (RuntimeError, ImportError) as e:
        log.warning(
            "EMBEDDING_MODEL=%s is unavailable (%s) — falling back to 'default'",
            settings.embedding_model, e,
        )
        vector_store = VectorStore(settings.chroma_dir, embedding_model="default")
    claude = ClaudeClient(
        api_key=settings.anthropic_api_key,
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
        assistant_name=settings.assistant_name,
        company=settings.assistant_tenant,
    )
    retriever = HybridRetriever(
        vector_store,
        pool_size=settings.retrieval_pool,
        alpha=settings.hybrid_alpha,
    )
    # If RERANK_PROVIDER is misconfigured (e.g. set to "cohere" but
    # COHERE_API_KEY is empty), refuse to crash the whole server — fall
    # back to the no-op reranker and warn loudly. The chat endpoint still
    # works, just without re-ranking. This matters because /health, the
    # admin panel, and the demo landings all live in the same process.
    try:
        reranker = make_reranker(
            settings.rerank_provider,
            cohere_api_key=settings.cohere_api_key,
        )
    except (ValueError, ImportError) as e:
        log.warning("Reranker config invalid (%s) — falling back to no-op", e)
        reranker = make_reranker("none")
    rag = RAGPipeline(
        retriever=retriever,
        claude=claude,
        top_k=settings.top_k,
        reranker=reranker,
        pool_size=settings.retrieval_pool,
    )
    ingestion = IngestionPipeline(
        db=db,
        vector_store=vector_store,
        upload_dir=settings.upload_dir,
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        on_change=lambda: retriever.invalidate(),
    )
    chat_service = ChatService(rag=rag, db=db)
    escalation_service = EscalationService(
        db=db,
        slack_webhook=settings.escalation_slack_webhook,
        email=settings.escalation_email,
        assistant_name=settings.assistant_name,
        tenant=settings.assistant_tenant,
    )

    app.state.db = db
    app.state.vector_store = vector_store
    app.state.claude = claude
    app.state.rag = rag
    app.state.ingestion = ingestion
    app.state.chat = chat_service
    app.state.escalation = escalation_service

    if not claude.configured:
        log.warning(
            "ANTHROPIC_API_KEY is not set — /api/chat will return 503. "
            "Add the key to .env and restart."
        )
    log.info(
        "Ready: collection=%s docs=%d chunks=%d",
        vector_store.collection_name,
        len(await db.list_documents()),
        await db.total_chunks(),
    )
    yield
    log.info("Shutting down")


def create_app(settings_override: Settings | None = None) -> FastAPI:
    settings = settings_override or get_settings()
    app = FastAPI(
        title="AI Chatbot with RAG",
        description=(
            "Embeddable AI assistant for company websites. "
            "FastAPI · Claude · ChromaDB."
        ),
        version=__version__,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.metrics = MetricsStore()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router)
    app.include_router(escalate.router)
    app.include_router(widget.router)
    app.include_router(admin.router)

    @app.middleware("http")
    async def observability_middleware(request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid4()))
        token = REQUEST_ID_CTX.set(request_id)
        start = perf_counter()
        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception:
            status_code = 500
            raise
        finally:
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path)
            app.state.metrics.observe(
                method=request.method,
                path=route_path,
                status=status_code,
                duration_seconds=perf_counter() - start,
            )
            REQUEST_ID_CTX.reset(token)
        response.headers["X-Request-ID"] = request_id
        return response

    # Mount the JS widget at /widget/* so any site can `<script>` to it.
    widget_dir = Path(__file__).parent.parent / "widget"
    if widget_dir.exists():
        app.mount("/widget", StaticFiles(directory=widget_dir), name="widget")

    # Mount the demo landings + admin panel under /demo/*.
    demo_dir = Path(__file__).parent.parent / "demo"
    if demo_dir.exists():
        app.mount("/demo", StaticFiles(directory=demo_dir, html=True), name="demo")

    @app.get("/", include_in_schema=False)
    async def root():
        index = demo_dir / "index.html"
        if index.exists():
            return FileResponse(index)
        return RedirectResponse(url="/docs")

    @app.get("/metrics", include_in_schema=False)
    async def metrics():
        return PlainTextResponse(
            app.state.metrics.render_prometheus(),
            media_type="text/plain; version=0.0.4",
        )

    return app


app = create_app()
