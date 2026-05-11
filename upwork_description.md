# Upwork portfolio description (ready-to-paste)

> **Canonical copy-paste pack lives in [`UPWORK_PORTFOLIO.md`](UPWORK_PORTFOLIO.md)**
> — that file maps 1-to-1 to the Upwork "Add Portfolio Item" form fields and
> has live URLs, image order, FAQ snippets and pricing tables already filled
> in. This file is the short summary used by the auto-bundler.

---

## Title (under 70 chars)
> **AI Chatbot with RAG for Company Websites — FastAPI + Claude + Chroma**

Alternative variants:
- *Embeddable AI Chatbot — Live Demo + Full Source — Claude + RAG + Vector DB*
- *Production AI Assistant for Any Website — One Script Tag, Drop In*
- *Custom GPT-style Chatbot for Your Site — Cited Answers from Your Docs*

---

## Description (~220 words)

End-to-end **AI chatbot with Retrieval-Augmented Generation (RAG)** that any
company can drop on its marketing site with **one `<script>` tag**. Built on
**FastAPI + Anthropic Claude + ChromaDB**, deployed in one Docker container,
no LangChain or LlamaIndex.

🔗 **Live demo (try it right now):** https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/
🔗 **Same backend, law-firm vertical:** https://ai-chatbot-rag-production-9637.up.railway.app/demo/law/
🔗 **Admin panel** (drop a PDF, watch the bot learn): https://ai-chatbot-rag-production-9637.up.railway.app/demo/admin/ — token `demo-please-do-not-abuse-1234567890` (demo KB is wiped regularly; please don't upload anything sensitive)
🔗 **Source code:** https://github.com/KirillHat/ai-chatbot-rag

What's in the box:

- 🤖 **Embeddable JS widget** — vanilla, ~28 KB raw / ~9 KB gzipped, zero dependencies. Theme + greeting per tenant via `data-*` attributes.
- 🌊 **Streaming responses (SSE)** — token-by-token like ChatGPT. Falls back to a blocking call if the host's proxy buffers SSE.
- 📚 **Document ingestion** — drag-and-drop **PDF, Markdown, plain text** in the admin panel. SHA-256 dedup, chunked, embedded, indexed in seconds. No retraining, no restart.
- 🔎 **Hybrid retrieval (BM25 + vector)** — keyword + semantic search fused via Reciprocal Rank Fusion. Optional Cohere re-ranking for +20-30% relevance.
- 🌍 **Multilingual** — flip one env var for 50+ languages including Russian, Spanish, German, Mandarin.
- 🤝 **Hand-off to a human** — captures contact + reason + transcript, fans out to Slack with built-in PII redaction.
- 📈 **Analytics dashboard** — sessions/7d, no-answer rate, top-5 questions, 30-day daily-volume chart, pending escalations.
- 🔐 **Production-grade** — sliding-window rate-limit, CORS allow-list, Bearer-token admin with constant-time compare, non-root Docker, Prometheus `/metrics`.
- 🚀 **One-command deploy** — Railway, Fly.io, Render templates. The live demo above runs on Railway.
- 🧪 **74 pytest tests, 6 CI jobs** — chunking, loaders, RAG, hybrid retrieval, streaming SSE, escalation, analytics, observability + security regressions. CI runs Python 3.10/3.11/3.12 + detect-secrets + Docker build.

Stack: **Python 3.11 · FastAPI 0.121 · Anthropic Claude Sonnet 4.6 · ChromaDB 0.5 · BM25 (custom, 50 LOC, no deps) · sentence-transformers (optional) · Cohere rerank (optional) · pypdf · pydantic · aiosqlite · Docker · GitHub Actions · Railway.**

---

## Skills / tags

`Python` · `FastAPI` · `AI Chatbot` · `Claude API` · `Anthropic` · `RAG` ·
`Retrieval-Augmented Generation` · `ChromaDB` · `Vector Database` ·
`Embeddings` · `LLM` · `Streaming SSE` · `Embeddable Widget` · `Docker` ·
`GitHub Actions` · `JavaScript` · `PDF Parsing` · `Knowledge Base` · `BM25` ·
`Multilingual` · `Async Python` · `pytest` · `REST API`

---

## Suggested cover & gallery images

- **Cover image:** `screenshots/cover.jpg` — split-screen of the hotel + law demos with the widget open on each
- **Gallery (8 shots in this order — first 4 are visible on the Upwork tile):**
  1. `screenshots/cover.jpg` — hero, both demos at once
  2. `screenshots/03_hotel_chat_with_answer.png` — **killer shot**: cited answer with `[1]` chip
  3. `screenshots/05_law_widget_open.png` — same widget rebranded for the law firm
  4. `screenshots/08_admin_analytics.png` — analytics dashboard
  5. `screenshots/07_admin_with_docs.png` — drag-and-drop admin
  6. `screenshots/01_hotel_landing.png` — full hotel landing
  7. `screenshots/04_law_landing.png` — full law landing
  8. `screenshots/06_admin_empty.png` — empty admin state

---

## Suggested rate / pricing

- **Hourly:** $40 – $60 / hr (with this single project in the portfolio)
- **Fixed (single-tenant install):** $800 – $2 000
- **Fixed (multi-tenant build, per-domain branding):** $2 000 – $4 500
- **Add-ons:**
  - OCR for scanned PDFs (Tesseract / Textract): +$400 – $1 000
  - SSO admin + audit log: +$400 – $800
  - Hand-off via Intercom / Zendesk / HelpScout: +$500 – $1 200
  - Cohere re-ranking: +$200 – $400
  - Voice / phone integration (Twilio / Vapi.ai): +$1 500 – $3 500

---

## Pinned first reply to a client

> Hi {{name}} — thanks for reaching out!
>
> Before I write a long proposal, three things to look at:
>
> 🔹 Live demo (hotel concierge): https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/
> 🔹 Same backend, law firm rebrand: https://ai-chatbot-rag-production-9637.up.railway.app/demo/law/
> 🔹 Admin panel — drop a PDF, watch the bot learn: https://ai-chatbot-rag-production-9637.up.railway.app/demo/admin/ (token `demo-please-do-not-abuse-1234567890`; the demo KB is wiped regularly — please don't upload anything sensitive)
>
> Source code (74 tests, green CI): https://github.com/KirillHat/ai-chatbot-rag
>
> What's the URL of the website you'd embed this on? I can spin up a branch
> with your branding and a sample of your KB and show you the live result
> before we even start the contract.

---

See [`UPWORK_PORTFOLIO.md`](UPWORK_PORTFOLIO.md) for the longer pack with FAQ
snippets, talking points, the full pricing table and the click-through
checklist.
