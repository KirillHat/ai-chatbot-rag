# Publishing checklist — from local code to live Upwork portfolio

You're here. The local code, tests, screenshots and git repo are ready.
This file is the runbook for the last three things you (the human) need
to do that I can't do for you.

**Total time:** ~45–60 minutes (one-time).

---

## ✅ Already done

- [x] All code, tests, docs (`README.md`, `widget/README.md`, `CHANGELOG.md`)
- [x] 17 Higgsfield photos for both demo landings
- [x] Demo knowledge base (10 markdown files → 36 chunks)
- [x] **8 portfolio screenshots** in `screenshots/` — production-grade
- [x] **Initial git commit** (104 files, branch `main`)
- [x] Deploy templates (`deploy/railway.json`, `deploy/fly.toml`, `deploy/render.yaml`)
- [x] `Procfile` for Heroku-style platforms (workers pinned to 1)
- [x] 90-second video script with Higgsfield prompts (`VIDEO_SCRIPT.md`)
- [x] Upwork description draft (`upwork_description.md`)

---

## 1️⃣ Push to GitHub (≈10 min)

> **Why:** Upwork clients vetting a $1000+ engagement always check the
> code. A public GitHub repo with green CI badge + clean commit history
> raises perceived quality enough to add $5–10/h to your effective rate.

```bash
cd upwork_portfolio/2_ai_chatbot_rag

# If you don't have gh CLI: `brew install gh && gh auth login`
gh repo create ai-chatbot-rag \
  --public \
  --source=. \
  --push \
  --description "Embeddable AI chatbot with RAG for company websites — FastAPI + Claude + ChromaDB. One <script> tag, drop on any site." \
  --homepage "https://your-app.fly.dev"   # update once you've deployed in step 2
```

Then in the GitHub UI:

1. **About** (right sidebar pencil): paste the homepage URL again, add topics:
   `ai-chatbot`, `rag`, `claude`, `fastapi`, `chromadb`, `embeddable-widget`,
   `customer-support`, `python`, `streaming-sse`, `multilingual`
2. **Settings → Pages**: leave off (we're not hosting from Pages, the
   demo is on Fly/Railway/Render)
3. **Settings → Actions → General → Workflow permissions**: read + write
   (so the badge can update)
4. Optional: pin the repo on your GitHub profile so it's the first thing
   any Upwork-client visiting your profile sees.

After the first push, the CI badge in `README.md` will go green within
a couple of minutes — that's the "this guy actually ships" signal.

---

## 2️⃣ Deploy publicly on Railway (≈10 min)

> **Why Railway specifically:** zero cold-start, $5/mo always-warm, the
> simplest deploy command of any platform. No volume-creation drama,
> no region picking, no min-machines tuning. The entire deploy is 6
> commands. For a portfolio demo seen by Upwork clients, "instant"
> matters more than "free with caveats" — a 5-10 second cold start
> reads as "broken" to a stranger evaluating you.

```bash
cd upwork_portfolio/2_ai_chatbot_rag

# 1. Install + auth (one-time)
brew install railway    # or: npm i -g @railway/cli
railway login           # opens browser

# 2. Create project + service in one go (workspace ID required for non-interactive)
WORKSPACE_ID=$(railway list --json | python3 -c "import json,sys; print(json.load(sys.stdin)[0]['workspace']['id'])")
railway init --name ai-chatbot-rag --workspace "$WORKSPACE_ID"
railway add --service ai-chatbot-rag \
  --variables "ADMIN_API_TOKEN=$(openssl rand -hex 24)" \
  --variables "HOST=0.0.0.0" \
  --variables "CORS_ORIGINS=*" \
  --variables "CHROMA_DIR=/app/data/chroma" \
  --variables "SQLITE_PATH=/app/data/app.db" \
  --variables "UPLOAD_DIR=/app/data/uploads" \
  --variables "ASSISTANT_NAME=AI Assistant" \
  --variables "ASSISTANT_TENANT=demo"
railway service ai-chatbot-rag                # link the new service to cwd

# 3. Persistent volume (Chroma + SQLite + uploads survive redeploys)
railway volume add --mount-path /app/data

# 4. Generate a public URL + first deploy
railway domain                                # prints https://...up.railway.app
railway up --detach                           # builds & ships the Dockerfile

# 5. Wire your Anthropic API key (mark as secret so it doesn't show in logs)
railway variables --set "ANTHROPIC_API_KEY=sk-ant-..."

# 6. Seed the demo KB + realistic analytics on the deployed instance
railway run python scripts/seed_knowledge_base.py
railway run python scripts/seed_demo_chats.py
```

### After deploy — 60-second smoke test

```bash
URL=$(railway domain | grep -oE 'https://[^ ]+')
curl -s "$URL/health" | jq               # status: ok if API key set, degraded if not
open "$URL/demo/hotel/"                   # try the chat
open "$URL/demo/law/"
open "$URL/demo/admin/"                   # paste the ADMIN_API_TOKEN you generated
```

### Why not Fly.io / Render?

- **Fly.io** — free tier is real, but `auto_stop_machines = "stop"` means a 5-10s cold-start. To remove it you set `min_machines_running = 1` (≈$2/mo) — at which point you've matched Railway's price but written 4× more config. Persistent volumes are also a separate `fly volumes create` step that has to match the region. Use it if you have a strong preference for full control over the runtime.
- **Render** — free tier idles after 15 min and the cold-start is 30-60 seconds. Acceptable for a hobby project but **not** for an Upwork demo where the client's first impression is the URL load time.
- **Cloud Run / GKE / EKS** — overkill for a single-replica demo. Worth it once you start landing $5k+ engagements with infra requirements.

### Update the GitHub homepage

```bash
gh repo edit KirillHat/ai-chatbot-rag --homepage "$URL"
```

---

## 3️⃣ Publish the Upwork portfolio item (≈10 min)

In your Upwork freelancer profile → **Portfolio** → **Add work**:

### Title (Upwork truncates at ~70 chars)

> AI Chatbot with RAG for Company Websites — FastAPI + Claude + Chroma

### Description (paste from `upwork_description.md`)

Use the body text under **"Description (≈220 words)"** in
`upwork_description.md`. Replace the two placeholders:

- The Railway URL → already wired in
- `link in profile` → your GitHub repo URL

### Skills / tags

Copy the list under **"Skills / tags"** in `upwork_description.md`.
Upwork lets you pick up to 15.

### Project images (in this order — Upwork's first 4 are all visitors see in preview)

1. `screenshots/03_hotel_chat_with_answer.png` — **THE** killer shot
   (cited answer, real-looking hotel landing)
2. `screenshots/05_law_widget_open.png` — proves "one stack, two verticals"
3. `screenshots/08_admin_analytics.png` — analytics dashboard, sells "this is a product"
4. `screenshots/07_admin_with_docs.png` — drag-and-drop admin
5. `screenshots/01_hotel_landing.png` — clean hero
6. `screenshots/04_law_landing.png` — second vertical

### Project URL

Your Railway deploy URL — `https://ai-chatbot-rag-production-9637.up.railway.app`
(Upwork shows this as "View project" button, very high click-through).

### Source code URL

Your GitHub repo URL.

---

## 4️⃣ (Strongly recommended) Record the 90-second demo video

`VIDEO_SCRIPT.md` has the full script with Higgsfield cutaway prompts.
~2 hours of work, ~$5 total cost (Higgsfield credits + ElevenLabs voice).

Increases discovery-call conversion 2-4× per industry data — easily worth
the time before posting your first proposal.

Upload as **animated GIF** or **MP4** to the Upwork portfolio gallery
(Upwork accepts both up to 100 MB / 5 minutes).

---

## 5️⃣ First proposal — pinned message draft

When a relevant job posting comes in, send something like this in the
first 60 seconds (the pinned-message section of `upwork_description.md`
has the full template; here's the short version):

> Hi {{name}}, before I write a long proposal — let me show you the work.
>
> 🔹 Live demo: https://your-app.fly.dev/demo/hotel/
> 🔹 Same backend, different vertical: https://your-app.fly.dev/demo/law/
> 🔹 Admin panel (drop a PDF, watch it learn): https://your-app.fly.dev/demo/admin/
>    Token for the public demo: `demo-please-do-not-abuse-1234567890`
> 🔹 Source: github.com/{{your-handle}}/ai-chatbot-rag
>
> What's the URL of the website where you'd embed this? I can spin up a
> branch with your branding and a sample of your KB and show you the
> live result before we even start the contract.

That last line is what closes deals. It moves the conversation from
"sales" to "let me show you a personalized version" in one sentence.

---

## Reference: what each portfolio piece is selling

| Piece | What it proves to the client |
|---|---|
| Live demo | The thing actually works, end-to-end |
| GitHub repo | The code is real and clean (not a low-effort wrapper) |
| Hotel + law-firm verticals | One install fits multiple industries → reusable for theirs |
| Admin upload flow | They can self-serve KB updates → no monthly billable hours |
| Citations on every answer | Reduces "AI hallucinated" objection → easier to sign legal/medical clients |
| Analytics dashboard | Operational visibility → upsell to monthly retainer |
| Hand-off to a human | "What if the bot doesn't know?" objection handled |
| Multilingual + streaming | Dollar-value features — most competing demos don't have them |
| 72 passing tests + CI badge | Engineering rigor signal → your effective rate goes up |

---

## Stopping point

Once **steps 1–3** are done, the portfolio piece is live and getting
seen. You can then:

- Apply to 5-10 Upwork jobs/day in the AI chatbot category
- Add this as the showcase piece on your LinkedIn / personal site
- Iterate based on which proposals get callbacks

Steps 4–5 are conversion optimisations — do them after the first
2-3 client conversations (you'll learn what to emphasise).
