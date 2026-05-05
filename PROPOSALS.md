# First-proposal templates by vertical

Five templates covering 90% of the AI-chatbot job postings on Upwork.
Pick the closest match, replace the `{{}}` placeholders, send within
**60 minutes** of the job being posted (response speed > proposal
length on Upwork).

**Universal rules** (applies to every template below):

- **Open with the live demo URL on the first line**, not "Hi, I see
  you're looking for…". Clients read the first line, decide if you're
  worth opening; the next 200 words only matter if line 1 hooked.
- **No more than ~150 words.** Long proposals look like template spam.
- **One specific question at the end** that requires the client to
  reply with information you'll need anyway. Doubles your reply rate.
- **No emojis at the start of paragraphs.** Reads cheap.
- **Replace `{{INDUSTRY_DETAIL}}` with something specific from the job
  post** (one sentence). Proves you read it.

---

## Template 1 — Hospitality / Hotel / Restaurant

Trigger words in job post: "hotel", "restaurant", "booking", "guests",
"reservations", "concierge", "front desk", "bookings", "Airbnb",
"property management".

```
Hi {{NAME}},

Quick way to evaluate the work before I write a long proposal —
I built and deployed a working hotel-concierge demo of exactly the
kind of bot you're describing:

  https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/

Open the chat in the bottom-right and try "What time is breakfast?"
or "Can I bring my dog?". Every answer cites the source document
([1] chip — click to expand). I uploaded 5 markdown files (room
rates, amenities, FAQ); the bot indexed them in seconds.

For your case ({{INDUSTRY_DETAIL}}), the fit is the same: I take
your existing PDFs / website pages / Google Docs, the bot answers
guest questions on your site 24/7 with citations to the actual
source. When the bot doesn't know, it offers to escalate to your
front desk (Slack notification with the conversation transcript).

What's the URL of your hotel site, and roughly how many pages /
PDFs of guest-facing info do you have? I can spin up a branded
preview with a sample of your KB before we even sign a contract.

Source code (open, MIT-licensed): github.com/KirillHat/ai-chatbot-rag
```

---

## Template 2 — Legal / Law Firm / Compliance

Trigger words: "law firm", "attorney", "legal", "NDA", "GDPR",
"compliance", "intake", "case", "client portal", "tax", "accountant".

```
Hi {{NAME}},

Before a long proposal — same kind of project you're describing,
deployed and live:

  https://ai-chatbot-rag-production-9637.up.railway.app/demo/law/

It's an AI assistant for a Boston law firm. Try "How much for an
NDA review?" or "Are you admitted in California?" — every answer
cites the source paragraph and refuses to answer questions outside
the firm's public knowledge base ("I don't have that information,
let me put you in touch with an attorney").

For {{INDUSTRY_DETAIL}}, the relevant pieces are:

  - Citation on every answer (mandatory for legal — clients can verify
    in two seconds, no "AI hallucination" objection).
  - Hard refusal when the answer isn't in the KB (the bot won't
    invent prices, deadlines, or jurisdictions).
  - Hand-off to a human via Slack / email when the bot doesn't know
    or when the user explicitly asks ("Talk to a human" button).
  - PII redaction on outbound transcripts (cards, SSNs, secrets).

Source: github.com/KirillHat/ai-chatbot-rag (74 tests, green CI)

What knowledge base would you load — public marketing pages,
internal handbook, or both? And do you need multilingual support?
```

---

## Template 3 — E-commerce / SaaS / Product

Trigger words: "ecommerce", "Shopify", "Woo", "online store",
"product catalog", "saas", "knowledge base", "documentation",
"customer support", "FAQ", "Zendesk", "Intercom".

```
Hi {{NAME}},

Live working demo of the same architecture:

  https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/

It's a different vertical (boutique hotel) but the building blocks
are identical to what you described — embeddable chat widget,
RAG over your own docs, streaming answers, citations.

For {{INDUSTRY_DETAIL}}, the relevant features are:

  - One-script-tag embed on any site (Shopify / Webflow / WordPress
    / your custom React app) — no plugin install, no theme edit
    beyond pasting a tag.
  - Self-serve admin: drop your product catalog / help-center
    PDFs / Notion exports, the bot indexes them in seconds.
  - Built-in analytics: which questions are asked most, what % the
    bot can't answer (so you know what KB content to add next),
    daily volume chart, escalation funnel.
  - Hand-off to your existing helpdesk (Slack / email; Intercom or
    Zendesk integration is +$500-$1200 add-on).

Source: github.com/KirillHat/ai-chatbot-rag

A few specifics so I can quote properly: which CMS / framework is
your site on, and roughly how many pages / products does your
KB cover?
```

---

## Template 4 — Healthcare / Clinic / Wellness

Trigger words: "clinic", "doctor", "patient", "appointment",
"healthcare", "medical", "dental", "wellness", "therapist", "spa".

⚠️ **Healthcare requires extra care.** Always disclaim "not medical
advice" and never let the bot answer treatment questions. Mention HIPAA
if the client is US-based.

```
Hi {{NAME}},

A working live demo of the same architecture (different vertical):

  https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/

For {{INDUSTRY_DETAIL}}, the medical-grade adjustments I'd make:

  - Hard prompt boundary: bot answers ONLY operational questions
    (hours, locations, what to bring, insurance accepted, how to
    book) and refuses anything resembling medical advice with
    "Please consult a clinician — let me schedule an appointment".
  - "Talk to a human" button on every screen, not just in the
    footer (one click, no friction).
  - PII redaction on outbound channels (built-in: SSNs, card
    numbers, secrets, partial email addresses).
  - On-prem deploy option if you're HIPAA-bound: I can swap the
    cloud Anthropic call for a self-hosted Llama 3 / Mistral via
    Ollama (~one-day swap, all KB stays inside your VPC).
  - Citation on every answer with the source document — the bot
    never makes up policies or prices.

Source: github.com/KirillHat/ai-chatbot-rag

To scope properly: are you US-based (HIPAA scope question), and do
you need on-prem or is cloud OK?
```

---

## Template 5 — Real estate / Local services

Trigger words: "real estate", "realtor", "property", "listing",
"agent", "broker", "service business", "local business", "agency".

```
Hi {{NAME}},

Live demo of exactly this architecture (different vertical):

  https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/

The hotel demo is incidental — the engine works on any
domain-specific KB. Open the chat, ask anything, the bot answers
with a citation to the source paragraph.

For {{INDUSTRY_DETAIL}}, the build looks like:

  - I take your listings / service descriptions / FAQ / process
    docs (PDF, Markdown, Google Docs export — drop into the admin).
  - The bot answers visitor questions on your site 24/7 with
    citations and refuses to invent details.
  - Lead capture: when a visitor wants to talk to a real agent, the
    "Talk to a human" button captures their contact + the chat
    transcript and notifies you on Slack / email. PII (cards, SSNs)
    is redacted from the outbound notification.
  - Analytics: which neighbourhoods / property types / price ranges
    visitors ask about most. Pure SQL over the chat log, useful for
    SEO and content strategy.

Source: github.com/KirillHat/ai-chatbot-rag

Two questions to scope: which CMS is your site on (WordPress /
Squarespace / custom), and roughly how many listings or service
pages should the bot know about?
```

---

## What NOT to send (lessons from Upwork's noise floor)

- ❌ "Hi, I'm a senior AI engineer with 10 years of experience"
- ❌ "I noticed your job and I'm very interested"
- ❌ "I have built many similar chatbots"
- ❌ Numbered lists of your past clients
- ❌ Mentioning OpenAI / GPT-4 if the client asked for Claude
  (and vice versa)
- ❌ Attaching a PDF "portfolio" — clients won't open it
- ❌ Asking for "more details about your project" without
  proposing anything
- ❌ Anything over 250 words

---

## When to skip the proposal

You'll save Connects (Upwork charges ~6 per proposal) by NOT
applying when:

- Budget is **fixed at <$300** for "AI chatbot for our website" with
  no further detail. The client doesn't yet know what they want;
  educating them costs you more than you'll bill.
- The job post says **"must use OpenAI"** — fine, you can swap, but
  the client has already pre-decided and won't value your stack.
- The job has **>30 proposals** within 4 hours of posting. Probably
  spam-applied to; client will pick by hourly rate, not quality.
- The client's **payment is unverified** AND it's their first job.
  Two red flags is enough.
- The client asks to **"start with a small free project"**. Always no.

## When to push hard (apply within 30 minutes)

- Budget **$1 000+** fixed OR **$50+/hr**
- Job post mentions **"production"**, **"existing site"**,
  **"our customers"** (real business, not hobbyist)
- Client has **payment verified + previous hires + good reviews**
- Job post has **<10 proposals so far** and is freshly posted
- Specific stack mentioned (FastAPI, Claude, RAG, Chroma, etc.)
  matches exactly what you have
