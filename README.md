# AI Chatbot with RAG — Embeddable Assistant for Company Websites

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)](.github/workflows/ci.yml)
[![Tests](https://img.shields.io/badge/tests-72%20passing-brightgreen)](tests/)
[![Streaming](https://img.shields.io/badge/streaming-SSE-purple)](app/api/chat.py)
[![Hybrid](https://img.shields.io/badge/retrieval-BM25%20+%20vector-blue)](app/core/retrieval.py)
[![Multilingual](https://img.shields.io/badge/i18n-50%2B%20languages-green)](app/core/vectorstore.py)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009485?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Claude](https://img.shields.io/badge/Anthropic-Claude%203.5%20Sonnet-D97757)](https://www.anthropic.com/claude)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.5-F09433)](https://www.trychroma.com)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ed?logo=docker&logoColor=white)](Dockerfile)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

A production-leaning **AI chatbot with Retrieval-Augmented Generation (RAG)** for any
company website. Drop one `<script>` tag on your marketing site, upload a PDF or
Markdown KB through the admin panel, and the bot answers visitor questions with
**inline citations** to the source document — no rebuild, no restart, no
LangChain.

> Built as a portfolio project to demonstrate a complete, no-handwaving
> RAG stack: FastAPI + Claude API + ChromaDB + an embeddable vanilla-JS
> widget + two industry-specific demo landings + a one-click admin panel.

**What clients see live:**

- 🏨 [`/demo/hotel/`](demo/hotel/index.html) — boutique-hotel landing with the AI concierge bottom-right
- ⚖ [`/demo/law/`](demo/law/index.html) — law-firm landing with the legal assistant, rebranded
- 🛠 [`/demo/admin/`](demo/admin/index.html) — admin panel: drop a PDF → indexed in seconds → bot answers from it on the next message

---

## 🆕 v1.1 — what's new

- 🌊 **Streaming responses (SSE)** — answers appear word-by-word in the
  widget like ChatGPT. `POST /api/chat/stream` emits `session`, `delta`,
  `citations`, `done` events; the widget falls back to the JSON endpoint
  if the stream is blocked by a proxy.
- 🤝 **Hand-off to a human** — "Talk to a human" button in the widget.
  Captures contact + reason + the conversation transcript and fans out
  to a Slack incoming-webhook (and/or logs an `ESCALATION_EMAIL_PAYLOAD`
  line for downstream relay).
- 📈 **Analytics dashboard** — admin panel now shows `sessions/7d`,
  `questions today`, `no-answer rate`, `avg msgs/session`, pending
  escalations, top-5 questions and a 30-day daily-volume chart. Pure
  SQL over `chat_messages`, no extra store.
- 🔎 **Hybrid retrieval (BM25 + vector via RRF)** — keyword search on
  top of semantic search, fused with Reciprocal Rank Fusion. Catches
  literal-token queries ("SOC 2", "GDPR Art 32") that pure embeddings
  glide past. Tunable via `HYBRID_ALPHA`.
- 🌍 **Multilingual embeddings** — set `EMBEDDING_MODEL=multilingual`
  to switch the default English-only ONNX MiniLM to
  `paraphrase-multilingual-MiniLM-L12-v2` (50+ languages incl. Russian).
- 🥇 **Optional re-ranking** — `RERANK_PROVIDER=cohere` sends the
  top-N candidates through `rerank-multilingual-v3.0` for a +20-30%
  retrieval-quality lift. Off by default.
- 🚀 **Deploy templates** — one-command deploy on Railway, Fly.io and
  Render. See [`deploy/README.md`](deploy/README.md).
- 📸 **Screenshot script** — Playwright capture of all 8 portfolio shots
  from a running instance. See [`scripts/capture_screenshots.py`](scripts/capture_screenshots.py).

## ✨ What this stack does

### For the website visitor
- A **floating chat launcher** in the bottom-right corner of every page it's embedded on
- Conversations are remembered across page reloads via `localStorage` session id
- Every answer carries **clickable `[1]` citations** that expand to show the source document and a 280-char snippet — no more "AI hallucinated this" arguments
- Polite refusal when the answer isn't in the KB ("I don't have that information — would you like me to put you in touch with our team?")
- **Mobile-friendly** (panel takes nearly full viewport below 480 px) and **a11y-aware** (`aria-label`, `role="dialog"`, keyboard-navigable)

### For the admin / business owner
- Upload **PDF, Markdown or plain text** through a drag-and-drop panel, no terminal needed
- See real-time stats: documents, total chunks, total characters
- Delete a document with one click — vectors and metadata removed atomically
- Token-protected (`Authorization: Bearer …`) — paste it once, persisted in `localStorage`

### For the operator / dev
- **One process, one image** — Chroma is embedded, SQLite for metadata, no external Postgres / Redis / vector-server needed
- **Zero LangChain / LlamaIndex** — everything is hand-written and ~600 lines of Python (you can read it all in a morning)
- Pluggable embedding model — currently the default ONNX MiniLM-L6-v2 (free, CPU); swap for OpenAI / Voyage / Cohere in [`vectorstore.py`](app/core/vectorstore.py) without touching anything else
- **Sliding-window per-IP rate limiter** on `/api/chat` to keep the bill predictable when the widget is on a public site
- **CORS-configurable** — embed the widget on any domain you whitelist
- **Docker-ready** — one-command deploy with persistent volume for vectors

---

## 🎬 Live demo flow

```
Visitor lands on /demo/hotel/
  ↓ taps the chat launcher
Widget GETs /api/widget/config             → tenant name, color, greeting
  ↓ types "What time is breakfast?"
Widget opens an SSE stream against /api/chat/stream
  ↓
Backend hybrid-retrieves top-K chunks (BM25 + vector via RRF) → Claude
streams the answer back token-by-token → widget paints each delta
  ↓
After the last delta: citations event with [1], [2] chips → done event
  ↓ user clicks [1]
Snippet of the source document expands inline
```

The widget falls back to the blocking `POST /api/chat` endpoint
automatically if the host is behind a proxy that buffers SSE
(set `data-streaming="false"` on the script tag to skip the streaming
attempt entirely). Both paths share the same RAG pipeline.

---

## 🧱 Architecture

```
                                ┌────────────────────────────────┐
                                │      FastAPI application       │
   <script src=widget.js>       │                                │
   ─────────────────────────────│  POST /api/chat                │
   widget rendered in browser   │   └─ ChatService.reply         │
   POST /api/chat               │       └─ RAGPipeline.answer    │
                                │            ├─ VectorStore.query (Chroma)
                                │            └─ Claude.complete  (Anthropic API)
                                │                                │
   Admin browser                │  POST /api/admin/documents     │
   ─────────────────────────────│   └─ IngestionPipeline         │
   drag & drop PDF              │       ├─ load_bytes (pypdf / utf-8)
                                │       ├─ split_text (recursive splitter)
                                │       ├─ Chroma.add (embed + persist)
                                │       └─ Database.add_document (SQLite)
                                └────────────────────────────────┘
                                              ▲          ▲
                                              │          │
                                  ┌───────────┴──┐  ┌────┴────────┐
                                  │  ChromaDB    │  │  SQLite     │
                                  │  (vectors)   │  │  (metadata) │
                                  └──────────────┘  └─────────────┘
```

Why both Chroma and SQLite? Chroma owns the vectors. SQLite owns the
human-readable metadata (filename, chunk count, upload time) and the chat
session/message log. Splitting them keeps the vector store hot-swappable —
you can swap Chroma for Qdrant or pgvector and the SQLite layer is unchanged.

---

## 🚀 Quick start

### 1. Clone and configure

```bash
git clone <this-repo>
cd 2_ai_chatbot_rag
python3.11 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

Open `.env` and fill in **at minimum**:

```ini
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx     # https://console.anthropic.com
ADMIN_API_TOKEN=pick-a-long-random-string-here-32-chars-or-more
```

### 2. Seed the demo knowledge base

```bash
python scripts/seed_knowledge_base.py
```

You should see:

```
Seeding from data/knowledge_base/hotel
  ✓ 01_general.md: 3 chunks (doc #1)
  ✓ 02_rooms_and_rates.md: 3 chunks (doc #2)
  ...
Vector store now holds 36 chunks across 10 documents.
```

The script is **idempotent** — re-running skips duplicates (sha-256 match).

### 3. Run

```bash
uvicorn app.main:app --reload
```

Then open:

- <http://localhost:8000/demo/hotel/> — hotel landing with AI concierge widget
- <http://localhost:8000/demo/law/> — law-firm landing with legal assistant
- <http://localhost:8000/demo/admin/> — admin panel (paste your `ADMIN_API_TOKEN` to log in)
- <http://localhost:8000/docs> — interactive OpenAPI docs (Swagger UI)
- <http://localhost:8000/health> — JSON health/version/document-count

---

## 🧩 Embedding the widget on your own site

```html
<!-- One tag, before </body>. That's it. -->
<script src="https://your-host.com/widget/chat-widget.js"
        data-api="https://your-host.com"
        data-name="Concierge Bot"
        data-greeting="Welcome to Hotel Aurora! How can I help?"
        data-primary="#A1845C"
        data-tenant="hotel-aurora"
        defer></script>
```

| Attribute       | Default                          | Notes                                                  |
| --------------- | -------------------------------- | ------------------------------------------------------ |
| `data-api`      | `window.location.origin`         | API base URL — useful when the widget is on `acme.com` and the bot lives on `bot.acme.com`. |
| `data-name`     | from `/api/widget/config`        | Header title.                                          |
| `data-greeting` | from `/api/widget/config`        | First message shown when the panel opens.              |
| `data-primary`  | from `/api/widget/config`        | Brand color — used for the launcher, header, user bubbles, send button, focus ring. |
| `data-tenant`   | `default`                        | Used as the `localStorage` key for the conversation id. Use a unique value per site. |
| `data-open`     | `false`                          | Set `"true"` to auto-open the panel on page load.      |

Full embed guide: [`widget/README.md`](widget/README.md).

---

## 📡 HTTP API

Full OpenAPI spec at `/docs` once the server is running. Quick reference:

### Public

```http
GET  /health                   → { status, version, document_count, chunk_count }
GET  /api/widget/config        → { name, greeting, theme, … }
POST /api/chat                 → { answer, citations, session_id, used_documents }
POST /api/chat/stream          → text/event-stream of {session,delta,citations,done}
POST /api/escalate             → 202 { id, status:"received", notified, message }
```

`POST /api/chat` payload:

```json
{
  "message": "What time is breakfast?",
  "history": [
    {"role": "user",      "content": "Can I check in early?"},
    {"role": "assistant", "content": "Early check-in from 12:00 for €25 …"}
  ],
  "session_id": "abc123…"
}
```

Response:

```json
{
  "answer": "Breakfast is served 07:00–10:30 in the Aurora dining room [1].",
  "citations": [
    {
      "document_id": 3,
      "document_name": "03_amenities.md",
      "snippet": "Breakfast hours 07:00–10:30 daily, 08:00–11:00 on Sundays …",
      "score": 0.84
    }
  ],
  "session_id": "5f8b4c2a…",
  "used_documents": 2
}
```

### Admin (Bearer-token protected)

```http
GET    /api/admin/documents       → { documents: [...], total_chunks: N }
POST   /api/admin/documents       multipart/form-data {file}  → DocumentOut
DELETE /api/admin/documents/{id}                             → 204
GET    /api/admin/analytics       → { sessions_*, no_answer_rate_7d,
                                      top_questions_7d, daily_volume_30d, … }
```

`Authorization: Bearer <ADMIN_API_TOKEN>` is required on every admin request.

---

## 📂 Project structure

```
2_ai_chatbot_rag/
├── app/
│   ├── main.py                 # FastAPI factory + lifespan + static mounts
│   ├── config.py               # pydantic-settings, env validation
│   ├── api/
│   │   ├── chat.py             # POST /api/chat + /api/chat/stream (SSE)
│   │   ├── admin.py            # /api/admin/documents + /api/admin/analytics
│   │   ├── escalate.py         # POST /api/escalate (hand-off to human)
│   │   ├── widget.py           # GET /api/widget/config (per-tenant theme)
│   │   ├── health.py           # GET /health
│   │   └── deps.py             # rate limiters (chat + escalate), auth
│   ├── core/
│   │   ├── claude.py           # Anthropic client: complete() + stream() + retries
│   │   ├── rag.py              # retrieve → (rerank) → generate → cite
│   │   ├── retrieval.py        # HybridRetriever: BM25 + vector via RRF (cached)
│   │   ├── reranker.py         # Optional Cohere rerank-multilingual-v3.0
│   │   └── vectorstore.py      # ChromaDB wrapper + multilingual embeddings
│   ├── ingestion/
│   │   ├── loaders.py          # PDF / Markdown / TXT, size & extension guards
│   │   ├── chunking.py         # recursive splitter (~LangChain semantics, no dep)
│   │   └── pipeline.py         # bytes → chunks → Chroma + SQLite + cache invalidate
│   ├── services/
│   │   ├── chat_service.py     # reply() + stream_reply() + session trust
│   │   └── escalation_service.py # Slack/email fan-out + PII redaction
│   ├── db/
│   │   └── database.py         # async SQLite: documents, sessions, messages, escalations
│   └── models/
│       └── schemas.py          # Pydantic request/response models
├── widget/
│   ├── chat-widget.js          # Embeddable vanilla-JS widget (~28 KB raw / ~9 KB gzipped)
│   └── README.md               # Embed guide
├── demo/
│   ├── index.html              # Pick-a-vertical landing
│   ├── hotel/index.html        # Hotel Aurora demo (concierge bot)
│   ├── law/index.html          # Bennett & Klein demo (legal assistant)
│   └── admin/index.html        # Drag-and-drop admin panel
├── data/
│   ├── knowledge_base/         # Bundled demo KBs (10 Markdown files)
│   ├── chroma/                 # Persistent vector store (gitignored)
│   ├── uploads/                # Original uploaded files (gitignored)
│   └── app.db                  # SQLite metadata (gitignored)
├── scripts/
│   └── seed_knowledge_base.py  # Bootstrap the demo KBs (idempotent)
├── tests/                      # 72 pytest tests across 10 files, ~30s total
├── deploy/                     # Railway / Fly.io / Render deploy templates
├── Procfile                    # Heroku-style platforms (workers pinned to 1)
├── CHANGELOG.md
├── VIDEO_SCRIPT.md             # 90-sec demo script + Higgsfield prompts
├── Dockerfile                  # Multi-stage, non-root, healthcheck
├── docker-compose.yml          # One-command deploy with persistent volume
└── .github/workflows/ci.yml    # Lint + test (3 Python versions) + Docker smoke
```

---

## 🧪 Tests

72 tests covering chunking, loaders, the database layer, the ingestion pipeline,
RAG citation extraction, hybrid retrieval (BM25 + RRF), re-ranker factory,
escalation flow, analytics shape, streaming SSE end-to-end, the public + admin
API surface, auth, rate-limiting, plus 7 security regressions
(session-id forgery, exception-text leak, admin-disabled probe, constant-time
token compare).

```bash
pip install -r requirements-dev.txt
pytest                           # everything, ~27s
pytest --cov=app --cov-report=html
ruff check .                     # lint, all checks pass
```

The test suite **never makes a network call to Anthropic** — the Claude client
is replaced with a deterministic stub via a fixture. ChromaDB and SQLite run
against a `tmp_path` directory per session, so tests never touch your real data.

GitHub Actions runs the suite on Python 3.10 / 3.11 / 3.12 plus a Docker
build + smoke test on every push.

---

## 🐳 Docker

One-command production deploy:

```bash
cp .env.example .env  &&  edit .env       # set ANTHROPIC_API_KEY + ADMIN_API_TOKEN
docker compose up -d --build
docker compose logs -f
```

The compose stack:

- Multi-stage Python 3.11-slim image (~150 MB), runs as non-root `app` user
- Persists Chroma + SQLite + uploads on the `chatbot-data` named volume
- Healthcheck against `/health` every 30 s
- Capped JSON logs (10 MB × 5 files)
- Restart `unless-stopped`

---

## ⚙ Configuration reference

All settings come from `.env`. Validated at boot — a typo fails the start-up,
not the first request.

| Variable                  | Default                          | What it does |
|---------------------------|----------------------------------|--------------|
| `ANTHROPIC_API_KEY`       | (empty → `/api/chat` returns 503) | Anthropic API key. |
| `CLAUDE_MODEL`            | `claude-3-5-sonnet-20241022`     | Any chat-capable Claude model. |
| `CLAUDE_MAX_TOKENS`       | `1024`                           | Max tokens in the assistant reply. |
| `ADMIN_API_TOKEN`         | `change-me` (admin disabled!)    | Bearer token for `/api/admin/*`. **Set this.** |
| `CHROMA_DIR`              | `./data/chroma`                  | Persistent vector store path. |
| `SQLITE_PATH`             | `./data/app.db`                  | Metadata + chat log DB. |
| `UPLOAD_DIR`              | `./data/uploads`                 | Original uploaded files. |
| `CHUNK_SIZE`              | `900`                            | Max chars per KB chunk. |
| `CHUNK_OVERLAP`           | `150`                            | Char overlap between adjacent chunks. |
| `TOP_K`                   | `4`                              | Number of chunks retrieved per query. |
| `RATE_LIMIT_PER_MINUTE`   | `20`                             | Per-IP sliding window on `/api/chat`. |
| `CORS_ORIGINS`            | `*`                              | CSV of allowed origins for the widget. |
| `HOST`                    | `0.0.0.0`                        | Bind address for uvicorn. Use `127.0.0.1` to keep the API local. |
| `PORT`                    | `8000`                           | Port for uvicorn. Match the `ports:` mapping in `docker-compose.yml`. |
| `ASSISTANT_NAME`          | `AI Assistant`                   | Header / system-prompt display name. |
| `ASSISTANT_TENANT`        | `demo`                           | Used in the system prompt as the company name. |
| `EMBEDDING_MODEL`         | `default`                        | `default` (English MiniLM), `multilingual` (50+ languages, needs `sentence-transformers`), or any sentence-transformers model id. |
| `RETRIEVAL_POOL`          | `16`                             | Wider candidate pool for hybrid search before trimming to `TOP_K`. Raise to 24-32 when re-ranking. |
| `HYBRID_ALPHA`            | `0.6`                            | 1.0 = pure vector, 0.0 = pure BM25, 0.6 = balanced (recommended). |
| `RERANK_PROVIDER`         | `none`                           | `none` (off) or `cohere` (uses `rerank-multilingual-v3.0`). |
| `COHERE_API_KEY`          | (empty)                          | Required when `RERANK_PROVIDER=cohere`. |
| `ESCALATION_SLACK_WEBHOOK`| (empty)                          | Slack incoming-webhook URL for hand-off events. |
| `ESCALATION_EMAIL`        | (empty)                          | Email address logged for downstream relay (no SMTP shipped). |

---

## 🔐 Production checklist

- [x] **Set `ADMIN_API_TOKEN`** to a strong random string. Default `change-me` returns 503 by design.
- [x] **Lock down `CORS_ORIGINS`** — replace `*` with the exact domains the widget will live on.
- [x] **Mount `./data` as a persistent volume** (already wired in `docker-compose.yml`).
- [ ] **Front the API with HTTPS** (Caddy / nginx / Cloudflare). The widget will only `fetch` over HTTPS once the host site is HTTPS.
- [ ] **Move rate-limiting to Redis** if you scale beyond one replica — the in-process limiter is per-replica only.
- [ ] **Pick a real embedding model** for non-English KBs. Set `EMBEDDING_MODEL=multilingual` to switch to `paraphrase-multilingual-MiniLM-L12-v2` (50+ languages, needs `pip install sentence-transformers`). For top-quality non-English retrieval combine with `RERANK_PROVIDER=cohere`. To plug in OpenAI / Voyage / a custom model, edit [`app/core/vectorstore.py:_embedding_function`](app/core/vectorstore.py).
- [ ] **Set up log shipping** if you want analytics — chat messages already land in SQLite (`chat_messages` table).
- [ ] **Tune `CHUNK_SIZE` / `TOP_K`** if your KB is large (>1k documents). The defaults are tuned for FAQ-sized corpora.

---

## 🧠 How RAG works here, in 5 lines

1. **Ingest:** PDF/Markdown → text → ~900-char overlapping chunks → embedded with MiniLM → stored in Chroma.
2. **Retrieve:** the user's question is embedded with the same model and the top-K nearest chunks are returned.
3. **Augment:** the chunks are pasted into a `<knowledge_base>` block above the user's question.
4. **Generate:** Claude answers the question, told to cite sources `[1] [2]`.
5. **Cite:** the `[n]` markers are parsed back into clickable chips that show the source document and snippet.

The whole pipeline lives in [`app/core/rag.py`](app/core/rag.py) (~30 lines) and
is the single seam to monkey-patch when you want to A/B different retrieval
strategies (re-ranking, HyDE, multi-query expansion).

---

## 📜 License

MIT — use it, fork it, ship it.

---

## 📬 Contact

Built by **Kirill Hat** as part of an Upwork freelance portfolio.
For commercial work, see [`upwork_description.md`](upwork_description.md).
