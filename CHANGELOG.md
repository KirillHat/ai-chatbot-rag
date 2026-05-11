# Changelog

All notable changes to this project are recorded here.

## [1.1.1] — 2026-05-11

### Added
- Two more security regression tests, bringing the suite to **74 tests, ~27 s**.

### Changed
- README and portfolio descriptions now consistently quote **74 tests** and
  **Anthropic Claude Sonnet 4.6** (the version the bundled config actually
  loads). Earlier copies of `upwork_description.md` quoted 72/50 tests and
  Claude 3.5 Sonnet — those were stale.

## [1.1.0] — 2026-05-02

### Added
- **Streaming SSE endpoint** ([`POST /api/chat/stream`](app/api/chat.py)) —
  `text/event-stream` of `session`, `delta`, `citations`, `done` events.
  Widget renders text token-by-token with a fall-back to `/api/chat`
  when the host blocks SSE. Driven by Anthropic's `messages.stream`.
- **Hybrid retrieval** ([`app/core/retrieval.py`](app/core/retrieval.py))
  — in-process BM25 (no external dep) fused with the existing Chroma
  vector channel via Reciprocal Rank Fusion. Tuned by `HYBRID_ALPHA`
  and `RETRIEVAL_POOL`.
- **Optional re-ranking** ([`app/core/reranker.py`](app/core/reranker.py))
  — `RERANK_PROVIDER=cohere` plugs in `rerank-multilingual-v3.0` for a
  +20-30% relevance lift; `none` is the default (no extra dep).
- **Multilingual embeddings** — `EMBEDDING_MODEL=multilingual` swaps
  the bundled English ONNX MiniLM for `paraphrase-multilingual-MiniLM-L12-v2`
  (50+ languages including Russian) via `sentence-transformers`.
- **Hand-off / escalation** ([`POST /api/escalate`](app/api/escalate.py))
  — "Talk to a human" button in the widget captures contact + reason +
  the conversation transcript, fans out to a Slack incoming-webhook
  and/or logs an `ESCALATION_EMAIL_PAYLOAD` line for downstream relay.
  Stored in a new `escalations` table.
- **Analytics dashboard** ([`GET /api/admin/analytics`](app/api/admin.py))
  — sessions/messages/no-answer-rate/avg-msgs/escalations + top-5 user
  questions + 30-day daily-volume chart. Pure SQL over `chat_messages`,
  rendered as inline bar chart in the admin panel.
- **Deploy templates** ([`deploy/`](deploy/)) — Railway, Fly.io, Render
  blueprints + a Heroku-style `Procfile`. One-command deploy with a
  persistent volume preconfigured.
- **Screenshot capture script** ([`scripts/capture_screenshots.py`](scripts/capture_screenshots.py))
  — Playwright headless capture of all 8 portfolio shots from a running
  instance, including admin panel after the demo KB was seeded.
- **22 new tests** — 15 in `test_features.py` (hybrid retrieval, RRF
  fusion, re-ranker factory, escalation happy-path + Slack-failure
  isolation, analytics shape + counts, streaming SSE end-to-end) and
  7 security regressions in `test_security.py` (session-id forgery,
  exception-text leak in chat log, admin-disabled-by-default 503,
  constant-time token comparison). Suite is now **72 tests, ~30 s**.

### Changed
- `RAGPipeline` now takes a `HybridRetriever` instead of a raw
  `VectorStore`. Backwards-compatible `pipeline.vector_store` shim is
  kept so older tests / custom code still works.
- `VectorStore.__init__` takes an `embedding_model` parameter.
- Chat error log now writes a static `(error)` marker to SQLite
  instead of the exception text — prevents accidental leakage of
  Anthropic error bodies into the chat history.
- Rate-limiter dict gets a 5-minute eviction sweep so a scanner
  hitting random IPs no longer leaks memory unboundedly.

### Security
- `session_id` from the client is now only honoured if the server has
  seen it before — pre-fix, an attacker could append messages to any
  forged uuid.
- Admin panel no longer hardcodes `/api/...` paths — `<body data-api>`
  lets you host the panel on a different origin from the API.
- Admin panel now clears bad tokens from `localStorage` on 401 instead
  of looping forever with a stale value.
- XSS hardening in the admin doc table — `source_type` whitelist +
  `escapeHtml` on every interpolated value.
- Tenacity retry covers `(APIError, APIConnectionError, APITimeoutError)`,
  not just the first — short network blips no longer surface as 503.

## [1.0.0] — 2026-05-02

Initial public release.

### Added
- **FastAPI backend** with three route groups:
  - `POST /api/chat` — public RAG chat (rate-limited, CORS-aware)
  - `POST/GET/DELETE /api/admin/documents` — Bearer-token-gated KB management
  - `GET /api/widget/config`, `GET /health` — public metadata
- **RAG pipeline** ([`app/core/rag.py`](app/core/rag.py)) — retrieve top-K
  Chroma chunks → render numbered context block → call Claude → parse `[n]`
  citations back into source documents (with a fall-back to the top retrieved
  chunk when the model forgets to cite).
- **Anthropic Claude client** ([`app/core/claude.py`](app/core/claude.py)) with
  a deliberately strict "answer only from context" system prompt and tenacity
  retries on transient `APIError`s.
- **ChromaDB wrapper** ([`app/core/vectorstore.py`](app/core/vectorstore.py)) —
  embedded Chroma, default ONNX MiniLM-L6-v2 embedding fn, cosine distance
  scaled to a `[0, 1]` similarity score.
- **Document ingestion** — `pypdf` for PDF, UTF-8 / Latin-1 fallback for
  Markdown / TXT, 25 MB upload cap, sha-256 dedup so re-uploads are no-ops.
- **Recursive text splitter** ([`app/ingestion/chunking.py`](app/ingestion/chunking.py)) —
  ~50 lines, same semantics as LangChain's `RecursiveCharacterTextSplitter`,
  zero dependency.
- **Async SQLite metadata layer** ([`app/db/database.py`](app/db/database.py)) —
  documents + chat sessions + per-message log with citations.
- **Embeddable JS widget** ([`widget/chat-widget.js`](widget/chat-widget.js)) —
  vanilla JS, ~12 KB at v1.0, zero deps. Theme + greeting + tenant per `data-*`
  attribute. Mobile-friendly, a11y-aware, click-to-expand citation chips.
- **Admin panel** ([`demo/admin/index.html`](demo/admin/index.html)) —
  drag-and-drop upload, live stats (docs / chunks / chars), per-document
  delete, token persisted in `localStorage`.
- **Two demo verticals** — boutique-hotel landing ([`demo/hotel/`](demo/hotel/index.html))
  and law-firm landing ([`demo/law/`](demo/law/index.html)) — both running on
  the same backend with per-tenant rebranding.
- **Bundled demo knowledge bases** — 10 Markdown documents (5 hotel, 5 law
  firm) covering FAQs, pricing, amenities, practice areas, intake checklists.
- **Idempotent seed script** ([`scripts/seed_knowledge_base.py`](scripts/seed_knowledge_base.py)) —
  bootstrap one or both demo KBs; safe to re-run.
- **Per-IP sliding-window rate limiter** for `/api/chat`, configurable via
  `RATE_LIMIT_PER_MINUTE`.
- **Bearer-token admin auth** with constant-time comparison; refuses to load
  if `ADMIN_API_TOKEN` is left at the default sentinel.
- **Docker** — multi-stage Python 3.11-slim build (~150 MB), runs as non-root
  `app` user, persistent `chatbot-data` volume, healthcheck on `/health`.
- **GitHub Actions CI** — lint (ruff) + test (pytest, Python 3.10/3.11/3.12)
  + Docker build & smoke test on every push.
- **50 pytest tests** covering chunking, loaders, the SQLite layer, the
  ingestion pipeline, RAG citation extraction, the public + admin API
  surface, auth and rate-limiting. Anthropic client is stubbed in tests so
  the suite never touches the network.

### Notes
- The default embedding model is **English-only**; for multilingual KBs swap
  the embedding function in [`vectorstore.py`](app/core/vectorstore.py).
- Streaming responses are intentionally not implemented — KB answers are
  short enough that perceived latency is dominated by Claude's TTFB.
- The in-process rate limiter is per-replica; for multi-replica deployments
  swap to Redis (one-day lift).
