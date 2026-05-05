# Upwork — copy-paste pack

Open this file next to the Upwork "Add Portfolio Item" form. Each
section maps 1-to-1 to a field on that form. Everything below is
final, sized, and has the live URL pre-baked.

---

## 1. Title (paste into "Title")

Pick **one**. Upwork truncates at ~70 chars in search results — these
all fit and were A/B-leaning to the front-loaded keywords clients
actually type.

> **AI Chatbot with RAG for Company Websites — FastAPI + Claude + Chroma**

Alternates if the first one feels overused:

- *Embeddable AI Chatbot — Live Demo + Full Source — Claude + RAG + Vector DB*
- *Production AI Assistant for Any Website — One Script Tag, Drop In*
- *Custom GPT-style Chatbot for Your Site — Cited Answers from Your Docs*

---

## 2. Description (paste into "Description" — Upwork allows ~6 000 chars)

End-to-end **AI chatbot with Retrieval-Augmented Generation (RAG)** that
any company can drop on its marketing site with **one `<script>` tag**.
Built on **FastAPI + Anthropic Claude + ChromaDB**, deployed in one
Docker container, no LangChain or LlamaIndex.

**🔗 Live demo (try it right now):**
https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/

**🔗 Same backend, different vertical:**
https://ai-chatbot-rag-production-9637.up.railway.app/demo/law/

**🔗 Admin panel — drop a PDF and watch the bot learn:**
https://ai-chatbot-rag-production-9637.up.railway.app/demo/admin/
(token: `demo-please-do-not-abuse-1234567890`)

**🔗 Source code (74 tests + green CI):**
https://github.com/KirillHat/ai-chatbot-rag

What's in the box:

🤖 **Embeddable JS widget** — vanilla, ~28 KB raw / ~9 KB gzipped, zero
dependencies. Drop on any HTML page. Theme + greeting per tenant via
`data-*` attributes.

🌊 **Streaming responses (SSE)** — answers stream in word-by-word like
ChatGPT. Auto-falls-back to a blocking call if the host's proxy buffers
SSE.

📚 **Document ingestion** — drag-and-drop **PDF, Markdown, plain text**
in the admin panel. Sha-256 dedup, chunked, embedded, indexed in
seconds. No retraining, no restart.

🔎 **Hybrid retrieval (BM25 + vector)** — keyword + semantic search
fused via Reciprocal Rank Fusion. Catches literal-token queries
("SOC 2", "GDPR Article 32") that pure embeddings glide past. Optional
Cohere re-ranking for a +20-30% relevance bump.

🌍 **Multilingual** — flip one env var (`EMBEDDING_MODEL=multilingual`)
for 50+ languages incl. Russian, Spanish, German, Mandarin.

🤝 **Hand-off to a human** — "Talk to a human" button captures contact +
reason + the conversation transcript and fans out to a Slack incoming
webhook (with built-in PII redaction for cards, SSNs, secrets, email
local-parts).

📈 **Analytics dashboard** — sessions today/7d, no-answer rate, top-5
questions, 30-day daily-volume chart, pending escalations. Pure SQL
over the chat log, no separate analytics store.

🛠 **Admin panel** — token-protected upload / list / delete + analytics.

🏨 **Two demo verticals** — boutique-hotel concierge bot + Boston
law-firm legal assistant. Both running on **one backend**, rebranded
per `data-tenant` and `data-primary` on the script tag.

🔐 **Production-grade** — sliding-window rate-limit (separate buckets
for chat + escalation), CORS allow-list, Bearer-token admin with
constant-time compare, session-id forgery defence, non-root Docker,
persistent volume, dynamic-port healthcheck, X-Request-ID correlation,
Prometheus `/metrics` endpoint.

🚀 **One-command deploy** — Railway, Fly.io and Render templates
included. The live demo above is on Railway (~$5/mo always-warm).

🧪 **74 pytest tests, 6 CI jobs** — chunking, loaders, RAG, hybrid
retrieval, streaming SSE, escalation, analytics, observability + 7
security regressions. CI runs Python 3.10/3.11/3.12 + detect-secrets +
runtime smoke + Docker build.

**Stack:** Python 3.11 · FastAPI 0.121 · Anthropic Claude Sonnet 4.6 ·
ChromaDB 0.5 · BM25 (custom, 50 LOC, no deps) · sentence-transformers
(optional) · Cohere rerank (optional) · pypdf · pydantic · aiosqlite ·
Docker · GitHub Actions · Railway.

---

## 3. Tags / Skills (paste 15 of these into the "Skills" field)

Upwork lets you pick up to 15. These are ranked by what clients
actually search for — keep them in roughly this order:

```
Python · AI Chatbot · Claude API · Anthropic · RAG · FastAPI ·
ChromaDB · Vector Database · LLM · Embeddings · Streaming SSE ·
JavaScript · Embeddable Widget · Docker · GitHub Actions
```

Bonus tags if Upwork suggests them:

- `Retrieval-Augmented Generation`, `PDF Parsing`, `Knowledge Base`,
  `Customer Support Automation`, `Multilingual`, `BM25`,
  `Async Python`, `pytest`, `REST API`

---

## 4. Project images (in this exact order)

Upwork's first **4** images are visible in the portfolio preview tile
(the rest only show after a click). Order matters — front-load the most
selling shots.

| # | File path | Why first |
|---|---|---|
| 1 | `screenshots/cover.jpg` | The hero — split-screen of both demos on two laptops. Sets the "one stack, multiple verticals" pitch instantly |
| 2 | `screenshots/03_hotel_chat_with_answer.png` | **THE killer shot** — cited answer with [1] citation chip on the hotel demo |
| 3 | `screenshots/05_law_widget_open.png` | Same widget rebranded for the law firm |
| 4 | `screenshots/08_admin_analytics.png` | Analytics dashboard — sells "this is a product, not a script" |
| 5 | `screenshots/07_admin_with_docs.png` | Drag-and-drop admin |
| 6 | `screenshots/01_hotel_landing.png` | Clean hero, full landing |
| 7 | `screenshots/04_law_landing.png` | Second vertical full landing |
| 8 | `screenshots/06_admin_empty.png` | Admin login screen |

Drag-and-drop the 8 PNGs into the Upwork uploader in this order.

---

## 5. Project URL (paste into "Project URL")

```
https://ai-chatbot-rag-production-9637.up.railway.app
```

This becomes the **"View project"** button on the Upwork tile —
extremely high click-through. Keep it pointing at the demo entry, not
the GitHub repo.

---

## 6. Source URL (paste into "Source code URL" if Upwork shows that field)

```
https://github.com/KirillHat/ai-chatbot-rag
```

---

## 7. Pinned welcome message (first reply in every chat)

When a client opens chat, paste this within 60 seconds:

```
Hi {{name}} — thanks for reaching out!

Before I write a long proposal, three things to look at:

🔹 Live demo (hotel concierge):
   https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/
🔹 Same backend, rebranded for a law firm:
   https://ai-chatbot-rag-production-9637.up.railway.app/demo/law/
🔹 Admin panel — drop a PDF, watch the bot learn:
   https://ai-chatbot-rag-production-9637.up.railway.app/demo/admin/
   token: demo-please-do-not-abuse-1234567890

Source code (74 tests, green CI): github.com/KirillHat/ai-chatbot-rag

What's the URL of the website you'd embed this on? I can spin up a
branch with your branding and a sample of your KB and show you the
live result before we even start the contract.
```

The last line is what closes the deal. Moves the conversation from
"you selling me" to "you've already done custom work for me".

---

## 8. Quick-reference FAQ (use these when clients ask in chat)

### "Why not LangChain?"

> LangChain pulls in ~80 packages and a moving API surface. Our whole
> RAG pipeline is **~30 lines** in one file (`app/core/rag.py`). The
> chunker is **~50 lines** with the same semantics as LangChain's
> RecursiveCharacterTextSplitter. Fewer dependencies, faster cold
> start, easier code audit — important for legal / healthcare clients
> with security review.

### "Why Claude and not GPT-4?"

> Anthropic's models score consistently higher on
> "answer-only-from-context" instruction following — exactly what RAG
> needs. Citation-following ([1] [2]) is more reliable on Claude.
> Pricing is competitive ($3/M input, $15/M output for Sonnet 4.6).
> Swapping to OpenAI / Mistral / your own LLM is a single-file change
> (`app/core/claude.py`) — the rest of the stack doesn't care.

### "What about hallucinations?"

> Three layers: (1) the system prompt forbids the model from answering
> when context is empty, (2) every claim shows a clickable citation
> with the exact 280-char snippet (the user can verify in two seconds),
> (3) for legal / medical domains we can surface the cosine similarity
> of the top retrieved chunk and refuse to answer below a threshold.

### "Do you handle multi-language KBs?"

> Yes. One env var: `EMBEDDING_MODEL=multilingual` switches us to
> `paraphrase-multilingual-MiniLM-L12-v2` (50+ languages including
> Russian, Spanish, German, Mandarin). Combine with
> `RERANK_PROVIDER=cohere` (`rerank-multilingual-v3.0`) for top
> non-English quality.

### "What about OCR for scanned PDFs?"

> Out of the box `pypdf` handles digital PDFs. For scans I add
> Tesseract or AWS Textract — usually adds ~$400-1 000 to the project
> depending on volume. Not bundled because most KBs are exported from
> Google Docs / Notion / Confluence and don't need OCR.

### "How fast does the answer arrive?"

> The streaming endpoint (`/api/chat/stream`) starts emitting tokens
> ~400-700 ms after submit (Claude's TTFB) and finishes a 200-token
> answer in ~3-5 s. The widget paints text token-by-token as it
> arrives, so perceived latency is dominated by the first token, not
> the full answer.

### "Can I run this on-prem / air-gapped?"

> Mostly yes. The vector DB (Chroma) and chunker run locally with no
> network. Only Claude needs the internet. For air-gapped, swap the
> Anthropic client for a self-hosted LLM (Llama 3 / Mistral via vLLM
> or Ollama) — same `claude.py` interface, ~100 LOC change.

---

## 9. Pricing positioning (in case the client asks before discovery)

```
Single-tenant install (one site, one KB, your branding):
  $800 – $2 000 fixed price, 2-5 working days.

Multi-tenant (multiple sites / multiple KBs from one backend, per-domain
branding, per-tenant analytics, per-tenant escalation channels):
  $2 000 – $4 500 fixed.

Common add-ons (price up-front, no surprises):
  - OCR for scanned PDFs (Tesseract / Textract): +$400 – $1 000
  - SSO admin login + audit log: +$400 – $800
  - Hand-off via Intercom / Zendesk / HelpScout: +$500 – $1 200
  - Cohere re-ranking for top relevance quality: +$200 – $400
  - Voice / phone integration (Twilio / Vapi.ai): +$1 500 – $3 500

Hourly (when fixed-price doesn't fit, e.g. ongoing iteration):
  $40 – $60 / hr depending on engagement size.
```

For comparable scope on Upwork (AI chatbot category), most fixed-price
jobs clear **$300 – $1 500**. With the live demo + cited-answer UX +
analytics + green CI, mid-to-upper end of that range is realistic from
day one. After 3-5 reviews you can quote double.

---

## 10. Ready-to-edit checklist (do this once, in order)

1. [ ] Open Upwork → **Profile** → **Portfolio** → **Add Project**
2. [ ] Paste **Title** (section 1)
3. [ ] Paste **Description** (section 2 — entire body)
4. [ ] Add the 15 **Skills** (section 3)
5. [ ] Drag-and-drop the 8 PNG files in the order from section 4
6. [ ] Paste **Project URL** (section 5) into "Project URL"
7. [ ] Paste **Source URL** (section 6) into the "URL" field if Upwork
       offers a separate one (newer profile UIs do)
8. [ ] **Save**, then click on the published item and verify the
       preview tile shows **cover.png** + 3 first screenshots cleanly
9. [ ] Pin the GitHub repo on your Upwork profile if Upwork lets you
       feature a project (the new "Featured Work" slot)
10. [ ] In the chat-snippets feature (Upwork Messenger has saved
        snippets in Settings) save the **section 7 pinned welcome
        message** as your default for new conversations.
11. [ ] Save the **section 8 FAQ** as 6 separate snippets so you can
        fire them with one keystroke when a client asks the obvious
        questions.
