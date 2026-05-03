# Upwork portfolio description (ready-to-paste)

---

## Title (under 70 chars — Upwork will truncate)

> **AI Chatbot with RAG for Company Websites — FastAPI + Claude + Chroma**

Alternative shorter variants:

- *Embeddable AI Assistant for Any Site — Claude + RAG + Vector DB*
- *Production AI Chatbot with PDF Knowledge Base + JS Widget*
- *Custom GPT-style Bot for Your Website — Cited Answers from Your Docs*

---

## Description (≈220 words — fits Upwork's project field cleanly)

End-to-end **AI chatbot with Retrieval-Augmented Generation (RAG)** that any
company can drop on its marketing site with **one `<script>` tag**. Built on
**FastAPI + Claude API + ChromaDB**, deployed in one Docker container, no
LangChain or LlamaIndex.

What's in the box:

- 🤖 **Embeddable JS widget** — vanilla, ~28 KB raw / ~9 KB gzipped, zero dependencies. Works on any HTML page. Theme + greeting per tenant via `data-*` attributes.
- 🌊 **Streaming responses (SSE)** — answers stream in word-by-word like ChatGPT; falls back to a blocking call automatically if the host's proxy buffers SSE.
- 📚 **Document ingestion** — drag-and-drop **PDF, Markdown, plain text** in the admin panel. Sha-256 dedup, chunked, embedded, indexed in seconds.
- 🔎 **Hybrid retrieval (BM25 + vector)** — keyword + semantic search fused via Reciprocal Rank Fusion. Catches literal-token queries ("SOC 2", "GDPR") that pure embeddings glide past. Optional Cohere re-ranking for an extra +20-30% relevance.
- 🌍 **Multilingual** — flip one env var (`EMBEDDING_MODEL=multilingual`) for 50+ languages incl. Russian/Spanish/German.
- 🤝 **Hand-off to a human** — "Talk to a human" button in the widget captures contact + reason + transcript and fans out to Slack (with built-in PII redaction).
- 📈 **Analytics dashboard** — sessions/7d, no-answer rate, top-5 questions, 30-day daily-volume chart, pending escalations. Pure SQL over the chat log.
- 🛠 **Admin panel** — token-protected upload / list / delete + analytics tab.
- 🏨 **Two demo verticals** — boutique-hotel concierge bot + law-firm legal assistant — both running on one backend, rebranded per site.
- 🔐 **Production-grade** — sliding-window rate-limit (separate buckets for chat + escalate), CORS allow-list, Bearer-token admin with constant-time compare, session-id forgery defence, non-root Docker, persistent volume, dynamic-port healthcheck.
- 🚀 **One-command deploy** — Railway, Fly.io and Render templates included.
- 🧪 **72 pytest tests** (chunking, loaders, RAG, hybrid retrieval, streaming SSE, escalation, analytics, security regressions). CI on Python 3.10/3.11/3.12 + Docker smoke build.

Stack: **Python 3.11 · FastAPI · Anthropic Claude 3.5 Sonnet · ChromaDB · BM25 (custom, 50 LOC, no deps) · sentence-transformers (optional) · Cohere rerank (optional) · pypdf · pydantic-settings · aiosqlite · Docker · GitHub Actions**.

**Live demo:** _(deploy URL goes here)_
**Code:** GitHub repo (link in profile)

---

## Skills / tags for the portfolio item

`Python` · `FastAPI` · `AI Chatbot` · `Claude API` · `Anthropic` · `RAG` ·
`Retrieval-Augmented Generation` · `ChromaDB` · `Vector Database` ·
`Embeddings` · `LLM` · `PDF Parsing` · `Knowledge Base` · `pypdf` ·
`SQLite` · `Async/Await` · `REST API` · `JavaScript` · `Embeddable Widget` ·
`Docker` · `GitHub Actions` · `Pytest`

---

## Suggested cover & gallery images

- **Cover image:** `screenshots/cover.png` — split screen of hotel + law demo with the widget open on each. Sets the "one stack, multiple verticals" pitch.
- **Animated demo:** `screenshots/demo.gif` — 30-second loop of the full flow: open hotel demo → ask 2 questions → expand a citation → switch to admin → upload a PDF → ask the bot about its content → answer comes back grounded in the upload.
- **Gallery (in this order, 6 shots is the sweet spot):**
  1. `screenshots/01_hotel_landing.png` — hotel landing page with the launcher in the corner
  2. `screenshots/02_widget_open_hotel.png` — widget open mid-conversation, citation chips visible
  3. `screenshots/03_widget_open_law.png` — same widget rebranded for the law firm
  4. `screenshots/04_admin_empty.png` — admin panel before any upload
  5. `screenshots/05_admin_uploading.png` — drag-and-drop in progress + stats updated
  6. `screenshots/06_architecture.png` — one-image stack diagram (FastAPI → Chroma + SQLite → Claude)

---

## Suggested rate / project pricing

- **Hourly rate** with this single project in the portfolio: **$30 – $55 / hr**
- **Fixed-price** for a similar bot with a single-tenant KB: **$800 – $2 000**
- **Multi-tenant build** (multiple KBs, per-domain branding, theme presets): **$2 000 – $4 500**
- **Add-ons:**
  - Custom embedding model (OpenAI / Voyage / multilingual): **+$200 – $500**
  - SSO admin + audit log: **+$400 – $800**
  - Streaming responses (SSE) instead of one-shot: **+$300 – $600**
  - Help-desk handover (Intercom / Zendesk / email): **+$500 – $1 200**
  - Analytics dashboard (queries / hit rate / no-answer rate): **+$600 – $1 500**

For comparable scope on Upwork, the AI chatbot category typically clears
**$300 – $1 500** per fixed-price job. With this demo and the cited-answer
UX, mid-to-upper end is realistic.

---

## What to demo on the discovery call

1. **The hotel landing.** Open the chat. Ask `"What time is breakfast?"`. Watch the answer come back with a `[1]` citation. Click it — the snippet expands to show the exact paragraph from `03_amenities.md`.
2. **The "I don't know" path.** Ask `"What's the password to the hotel Wi-Fi printer?"` (not in the KB). Bot politely says it doesn't have that and offers to escalate.
3. **The same widget on a different site.** Switch to the law-firm landing. Same launcher, brand-blue instead of brand-gold, different greeting. Same backend.
4. **Live KB upload.** Open `/demo/admin/`, paste the admin token, drop a PDF. Watch the stats update. Switch back to the chatbot — ask a question only that PDF can answer. Answer comes back cited to the new file.
5. **Open `/docs`.** Show the OpenAPI spec. Show that `POST /api/chat` is one endpoint, one payload, one response.
6. **Show the test suite.** `pytest -q` → 50 passed in 27 s. Show that the Anthropic client is mocked so the suite doesn't need an API key.
7. **Show `docker compose up`.** The whole thing is one image.

---

## Pinned message to send in the first reply to a client

When a client opens chat, send something like this in the first 60 seconds:

> Hey {{name}}, thanks for reaching out!
>
> Quick links so you can evaluate the work before deciding:
>
> 🔹 Live demo (hotel concierge): _(deploy URL)_/demo/hotel/
> 🔹 Live demo (law firm assistant): _(deploy URL)_/demo/law/
> 🔹 Admin panel (drop a PDF, watch the bot learn): _(deploy URL)_/demo/admin/
> 🔹 OpenAPI docs: _(deploy URL)_/docs
> 🔹 Source code: github.com/{{your-username}}/ai-chatbot-rag
>
> The admin token for the public demo is `demo-please-do-not-abuse-1234567890` —
> please don't upload anything sensitive, the demo KB is wiped daily.
>
> Happy to walk you through the architecture on a quick call, or scope what
> would need to change to fit your business — every part of the pipeline
> (vector store, embedding model, system prompt, citation UX) is a 30-minute
> swap.

---

## Talking points if the client asks "why not LangChain?"

- LangChain is great for prototyping, but adds ~80 packages, a moving API surface and a layer of indirection that makes debugging harder.
- The whole RAG pipeline here is **~30 lines** in one file ([`app/core/rag.py`](app/core/rag.py)).
- The chunker is **~50 lines** with the same semantics as `RecursiveCharacterTextSplitter`.
- This means **fewer dependencies**, **faster cold start**, **easier audit** — a real consideration for legal / healthcare clients.
- If you genuinely want LangChain it's a one-day swap — the seam is `RAGPipeline.answer`.

## Talking points if the client asks "why Claude and not GPT-4?"

- Anthropic's models score consistently higher on instruction-following for *"answer only from context"* tasks — exactly what RAG needs.
- Citation-following ([1] [2]) is more reliable on Claude in our experience.
- Pricing is competitive ($3 / 1M input, $15 / 1M output for Claude 3.5 Sonnet).
- Swapping to OpenAI is a **single file change** ([`app/core/claude.py`](app/core/claude.py)) — the rest of the stack doesn't care which provider answers.

## Talking points if the client asks "what about hallucinations?"

- The system prompt forbids the model from answering when the context is empty.
- Every claim shows a clickable citation with the exact 280-char snippet — clients can verify in two seconds.
- For legal / medical domains, we can also surface "confidence" (the cosine similarity of the top retrieved chunk) and refuse to answer below a threshold.

---

## What's *not* in scope for this template (and what they'd cost)

| Ask | Why it's not bundled | Approx. add-on |
|-----|---------------------|----------------|
| OCR for scanned PDFs | `pypdf` extracts text; scans need Tesseract or AWS Textract. | +$400 – $1 000 |
| OAuth admin login | Bearer-token is enough for a single admin; SSO needs a real IdP integration. | +$400 – $800 |
| Hand-off via Intercom/Zendesk/HelpScout | Slack webhook + PII-redacted transcript is built-in; first-class CRM integrations are per-vendor. | +$500 – $1 200 |
| Real SMTP for email escalations | We log a structured `ESCALATION_EMAIL_PAYLOAD` line for downstream relay; first-party SMTP needs Postmark / SES / SendGrid wiring. | +$200 – $500 |
| Per-tenant isolation (one Chroma collection per customer, one admin token per customer) | Currently single-tenant by design — multi-tenant needs row-level scoping. | +$800 – $2 000 |
| Voice / phone integration (Twilio, Vapi.ai) | Different I/O entirely — needs a Twilio account, voice-tuned prompts, latency budget. | +$1 500 – $3 500 |
