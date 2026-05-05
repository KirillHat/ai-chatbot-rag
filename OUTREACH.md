# Upwork outreach playbook

How to find AI-chatbot work that matches this portfolio piece, fast.
The goal is **3-5 quality proposals/day in 30 minutes**, not "blast
50 jobs in three hours".

---

## 1. Saved searches (set these up once, then check the feed)

Upwork → **Find Work** → **Saved Searches** → **+ New Saved Search**.
Set up these four, in priority order. Each one becomes an alert email.

### Search A — "AI chatbot for website" (highest hit rate)

```
Keywords:    AI chatbot OR RAG chatbot OR custom chatbot OR
             "embed chatbot" OR "GPT chatbot" website
Category:    AI Apps & Integrations  +  Web Development
Budget:      Fixed-price ≥ $500   OR   Hourly ≥ $30
Job type:    Hourly + Fixed
Client:      Payment verified
Posted:      Last 24 hours
Proposals:   Less than 5  (very important — filter the noise)
Sort:        Newest
```

This is the bread-and-butter feed. ~5-15 jobs/day match.

### Search B — "RAG / vector / Claude" (high quality)

```
Keywords:    RAG OR "retrieval augmented" OR Claude OR Anthropic OR
             ChromaDB OR "vector database" OR Pinecone OR Weaviate
Category:    AI Apps & Integrations  +  AI / Machine Learning
Budget:      Fixed-price ≥ $1 000   OR   Hourly ≥ $50
Posted:      Last 24 hours
Proposals:   Less than 10
Sort:        Newest
```

Lower volume (~1-3/day) but **way higher conversion** because the
client already knows exactly what they want and your stack matches.

### Search C — "company-specific AI assistant"

```
Keywords:    "AI assistant" OR "FAQ bot" OR "knowledge base bot" OR
             "support bot" OR "documentation bot"
             website OR Shopify OR WordPress OR Webflow
Category:    AI Apps & Integrations
Budget:      Hourly ≥ $30
Posted:      Last 7 days
Proposals:   Less than 15
Sort:        Newest
```

Reuse-leaning — these are often companies upgrading from a rule-based
bot to an LLM one. They've already approved the budget; "better than
their current" is an easy bar.

### Search D — Specific verticals (rotate weekly)

Switch one of these in once Search A-C are saturated:

```
Hospitality/hotels:    hotel AI OR hotel chatbot OR concierge bot
Legal:                 law firm chatbot OR legal AI assistant OR NDA review
Real estate:           "real estate" chatbot OR property AI assistant
Healthcare/clinic:     medical chatbot OR clinic FAQ AI
SaaS support:          "customer support" AI OR helpdesk AI bot
```

When applying to one of these, use the matching template from
[`PROPOSALS.md`](PROPOSALS.md).

---

## 2. The 60-second triage flow

When a job alert comes in, decide **apply / skip** in under a minute
using this checklist. If anything in the **red column** applies, skip;
otherwise apply.

| Signal | 🟢 Apply | 🔴 Skip |
|---|---|---|
| Client | Payment verified · Previous hires with good reviews | New client · No verification · 0 reviews |
| Budget | $500+ fixed · $30+/hr | <$300 fixed · "negotiable" with no number |
| Proposals so far | <10 | >30 in <4 h |
| Job post length | ≥3 specific paragraphs · technical detail | "Need a chatbot" · 1 line · vague |
| Their stack mention | Claude / FastAPI / RAG / specific KB type | "Maybe ChatGPT, maybe Llama, you decide" |
| Asks | One specific deliverable (a working bot on their site) | "Whole AI strategy" · "many features" |
| Tone | Professional · realistic timeline | "ASAP" · "tonight" · multiple exclamation marks |
| Location | Any | Match the "must be in [country]" if specified — never ignore |
| Currency | USD / EUR / GBP | Currency you've never been paid in |

Score 0 red → apply. 1 red → think before applying. 2+ red → skip and
preserve Connects.

---

## 3. Connects budget

Upwork charges ~6 Connects per proposal (varies by job). On the basic
plan you get 10 free + buy more at $0.15/Connect.

**Daily Connects budget: 30 (≈5 proposals).** Higher means you're
spamming.

If you start the day with 30 Connects and end the day with all 30
spent and 0 callbacks:

- Are you applying to **<$500 jobs**? Stop, raise the floor.
- Is your **proposal length >250 words**? Cut.
- Is your **first line "Hi, I am a senior engineer"**? Rewrite — first
  line should be the live demo URL.
- Are you **applying >30 minutes after the post**? Sort by Newest and
  apply faster.

---

## 4. Profile tuning (do once)

Critical: your **profile title** + **first 280 chars of your overview**
are what shows up in search. Same UX rules as the proposal: front-load
the keywords clients search for.

### Recommended profile title (under 70 chars)

> **AI Chatbot · RAG · Claude API · FastAPI · Embeddable Widget**

### Overview opener (first 280 chars are visible without expand)

> I build production AI chatbots with RAG (Retrieval-Augmented
> Generation) for company websites. Drop one `<script>` tag, the bot
> learns from your PDFs, and answers visitor questions with citations
> to the source document.
>
> Live demo: https://ai-chatbot-rag-production-9637.up.railway.app/demo/hotel/
> Code: github.com/KirillHat/ai-chatbot-rag

The full overview can be longer; the part above is what shows in
search results.

### Hourly rate

Start at **$45-55/hr**. Without reviews, going below $40/hr screams
"low quality"; clients budget AI projects at $50-100/hr and will
filter you out as "too cheap to be real". After 3 reviews, raise to
**$60-75/hr**.

### Featured Work slot

Pin the **portfolio item you just published** (the one driven by
[`UPWORK_PORTFOLIO.md`](UPWORK_PORTFOLIO.md)) as your single Featured
Work. Don't fill the slot with multiple projects of mixed quality —
one strong demo > five mediocre ones.

---

## 5. Daily routine (30 minutes/day)

1. **Open Upwork → Job alerts**. Read 5-10 fresh ones.
2. **Triage** with the table above. Identify ~3-5 to apply to.
3. **For each one**:
   - Open the job
   - Pick the right [`PROPOSALS.md`](PROPOSALS.md) template
   - Replace `{{NAME}}`, `{{INDUSTRY_DETAIL}}` (one sentence from the post)
   - Submit
4. **Note callbacks** in any spreadsheet (or Notion / sticky note).
5. **Reply to callbacks within 4 hours** — Upwork's algorithm
   penalises slow replies, and clients in active hiring mode talk to
   3-5 freelancers in parallel.

That's it. 30 minutes/day, sustained for 2 weeks, should produce 3-5
real conversations and 1-2 contracts.

---

## 6. After the first 3 contracts

Once you have **3 jobs completed with 5★ reviews** (≈3-6 weeks of
the routine above), you can:

- Raise the price floor: skip everything <$1 000.
- Raise the hourly: $75-90/hr.
- Stop applying — you'll start getting **invites** instead.
- Pin **two** Featured Works (the original portfolio + your best
  client testimonial).

The first 3 reviews are the unlock — that's the whole game.

---

## 7. Other channels (after Upwork is producing)

If Upwork is consistently producing $4-5K/mo and you want to grow:

- **LinkedIn**: post a 60-sec video demo of the live bot (script in
  [`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md)) once a week, tag with
  `#aichatbot #rag #claude`. Slow-burn but compounding.
- **Twitter / X**: same video, faster cycle, lower conversion.
- **HackerNews "Show HN"**: post the GitHub repo with the live demo
  link. One shot — if it makes the front page you'll get 50K+ views in
  a day. Has to be polished (which it is).
- **Indie Hackers / Reddit r/SideProject**: lower stakes than HN, can
  re-post a version of the same after.
- **Cold outreach**: scrape companies whose websites have a rule-based
  chatbot, send a 3-line email pointing at the live demo. 1-3% reply
  rate is normal.

Each of these is its own playbook — don't try to run all of them in
parallel until Upwork is in autopilot.
