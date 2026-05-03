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

## 2️⃣ Deploy publicly (≈30 min, recommended: Fly.io)

> **Why:** Upwork clients won't book a discovery call without touching
> the demo first. Without a public URL the entire portfolio piece is
> theoretical.

### Pick one of three platforms

| Platform | Cost | Cold start | Best for |
|---|---|---|---|
| **Fly.io** | Free tier (3 shared VMs) or ~$2-3/mo always-on | 5-10s after idle | Independent freelancer demo, full control |
| **Railway** | $5/mo always-warm | None | Want zero-fuss "always works" |
| **Render** | Free tier (idle after 15min) or $7/mo | 30-60s on free | One-click via blueprint, generous free tier |

### My recommendation: Fly.io with `min_machines_running = 1`

Adds ~$2-3/mo but eliminates the "oops the demo took 10 seconds to
respond, looks broken" first impression. Decisive for portfolio use.

```bash
# 1. Install + auth
brew install flyctl    # one-time
fly auth login         # opens browser

# 2. Create the app and the persistent volume
fly launch --copy-config deploy/fly.toml --no-deploy
# It'll ask:
#   App name: ai-chatbot-rag-<your-suffix>   (must be globally unique)
#   Region:   pick one near your target clients (iad / ams / fra / sin)
#   Postgres: NO
#   Redis:    NO
#   Deploy now: NO

fly volumes create chatbot_data --region <same-region> --size 1
# 1 GB is plenty — Chroma + SQLite for ~5k chunks fits in <100 MB

# 3. Set the secrets (these never end up in git, only on Fly's server)
fly secrets set \
  ANTHROPIC_API_KEY=sk-ant-API03-... \
  ADMIN_API_TOKEN=$(openssl rand -hex 24) \
  ASSISTANT_NAME="AI Assistant" \
  ASSISTANT_TENANT="demo"

# 4. Bake in always-warm before deploying
sed -i '' 's/min_machines_running = 0/min_machines_running = 1/' deploy/fly.toml
git add deploy/fly.toml && git commit -m "Pin always-warm machine for portfolio"

# 5. Deploy
fly deploy
fly status                              # should show 1 running machine
fly open                                # opens https://your-app.fly.dev
```

### After deploy — 60-second smoke test

```bash
URL=https://your-app.fly.dev    # use whatever fly assigned

# /health: status: "ok" if API key works, "degraded" otherwise
curl -s "$URL/health" | jq

# Demo landings
open "$URL/demo/hotel/"          # try chatting!
open "$URL/demo/law/"
open "$URL/demo/admin/"          # paste your ADMIN_API_TOKEN
```

### Then re-seed the demo KB on the deployed instance

The demo KB is bundled in the image at `data/knowledge_base/` but isn't
auto-loaded into Chroma — first ingestion happens lazily. Easiest way:

```bash
fly ssh console
cd /app
python scripts/seed_knowledge_base.py
python scripts/seed_demo_chats.py    # makes the analytics tab look populated
exit
```

### Update the URL in your docs + push

```bash
# Use sed to swap the placeholder in every file at once.
PUBLIC=https://your-app.fly.dev
grep -rl "_(deploy URL goes here)_\|_(deploy URL)_" \
  README.md upwork_description.md VIDEO_SCRIPT.md demo/ widget/README.md \
  | xargs sed -i '' "s|_(deploy URL goes here)_|$PUBLIC|g; s|_(deploy URL)_|$PUBLIC|g"

# Commit the URL changes
git add -A && git commit -m "Wire deployed URL into docs"
git push
```

---

## 3️⃣ Publish the Upwork portfolio item (≈10 min)

In your Upwork freelancer profile → **Portfolio** → **Add work**:

### Title (Upwork truncates at ~70 chars)

> AI Chatbot with RAG for Company Websites — FastAPI + Claude + Chroma

### Description (paste from `upwork_description.md`)

Use the body text under **"Description (≈220 words)"** in
`upwork_description.md`. Replace the two placeholders:

- `_(deploy URL goes here)_` → your Fly URL
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

Your Fly deploy URL — `https://your-app.fly.dev/` (Upwork shows this as
"View project" button, very high click-through).

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
