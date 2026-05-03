# 90-second portfolio demo — script + asset list

A polished `~90 s` voice-over demo for Upwork outreach and the portfolio
gallery. Split into 6 beats. Each beat lists what's on screen, what the
voice-over says, and what to capture (screen recording or Higgsfield
b-roll).

**Convention:**
- *(SR)* = screen recording from your local machine
- *(BR)* = b-roll cutaway, generated via Higgsfield
- *(VO)* = voice-over (English; record in ElevenLabs Antoni or Adam, ~155 wpm)

---

## Beat 1 — Hook (0–10 s)

**On screen:** *(SR)* Hotel landing page, hero in view. Mouse drifts down
toward the chat launcher.

**(VO):** *"This is an AI chatbot you drop on any company website with
one script tag. It learns from your PDFs and answers in seconds —
with citations to the source."*

**Capture:** Screen recording 1440×900, ~10 s, no audio (you'll dub VO).

---

## Beat 2 — Real conversation (10–28 s)

**On screen:** *(SR)* Chat launcher click → panel opens → user types
`"What time is breakfast?"` → answer streams in word-by-word →
`[1]` chip appears → user clicks it → snippet of `03_amenities.md`
expands inline.

**(VO):** *"Visitor asks. The bot streams its answer like ChatGPT,
grounded only in your knowledge base. Every claim has a clickable
citation — they can verify the source in two seconds."*

**Capture:** ~18 s screen recording. Make sure streaming is visible
(if your VPS proxy buffers SSE, set `STREAMING=true` in widget +
proxy `proxy_buffering off;`).

---

## Beat 3 — Multi-tenant (28–42 s)

**On screen:** *(SR)* Quick cut to law-firm landing. Same launcher,
different brand color. Open it. Ask `"What does an NDA review cost?"` →
streamed answer with `[1]` citation to `03_pricing_and_intake.md`.

**(VO):** *"One backend, many sites. The same code now answers as a
boutique law firm — different brand, different knowledge base, no
rebuild."*

**Capture:** ~14 s screen recording, mostly the answer streaming.

---

## Beat 4 — The wow moment: live KB upload (42–62 s)

**On screen:** *(SR)* Switch to admin panel. Drag a fresh PDF onto the
drop zone. Toast "Indexed → 12 chunks". Switch back to hotel widget,
ask a question only that PDF can answer. Bot answers, citing the new doc.

**(VO):** *"And the live demo for the client. You drop a PDF here…
twelve chunks indexed in seconds… and the bot answers from it on
the very next message. No retrain, no restart, no LangChain."*

**Capture:** ~20 s screen recording. This is the killer beat — let it
breathe, no cuts.

---

## Beat 5 — Analytics and hand-off (62–78 s)

**On screen:** *(SR)* Scroll to analytics tab — show the bar chart and
top questions. Then back to widget → "Talk to a human" button →
escalation submitted → Slack notification on the right side of the
screen.

**(VO):** *"Built-in analytics show what visitors actually ask, what
the bot couldn't answer, and how busy it is. And when the bot doesn't
know — one click puts a real human on it, with the full transcript."*

**Capture:** ~16 s screen recording.

---

## Beat 6 — Tech + CTA (78–90 s)

**On screen:** *(BR)* Generated cutaway — clean tech montage:
FastAPI logo → Claude logo → Chroma logo. Then text overlay:
"`docker compose up -d`" then "$800–2,500 / install".

**(VO):** *"FastAPI, Claude, ChromaDB, one Docker container. Eight
hundred to twenty-five hundred dollars per install. Link in the
description — let's talk about your site."*

---

## Higgsfield cutaway prompts (only Beat 6 needs generation)

These are the prompts for the only beat that's not a screen recording.
Each is a 5-second `seedance_2_0` clip; chain three together.

### Cutaway A — code editor zoom (3 s)

```
Photorealistic close-up overhead shot of a clean dark-mode VS Code
editor window. The visible file is `app/main.py` showing a FastAPI
app factory with imports of fastapi, anthropic and chromadb. Sharp
text, syntax-highlighted (purple keywords, green strings, orange
function names). Soft warm tungsten light from upper left, subtle
shallow depth at the corners. The cursor blinks gently next to a
line. Shot on Sony FX9, 50mm prime, f/2.8, no people, no hands,
sharp readable code.
```

### Cutaway B — server boot in terminal (4 s)

```
Photorealistic close-up of a clean dark-mode terminal window
showing the output of `docker compose up`. Visible lines:
"✓ Container ai-chatbot-rag  Started", "INFO uvicorn running on
http://0.0.0.0:8000", "INFO app.main: Ready: docs=10 chunks=36".
Faint CRT-style scanlines for character. Cursor blinks under the
last line. Photorealistic, sharp readable text, no morphing of
letters or numbers, locked-off camera with very subtle organic
drift, soft warm tungsten light, Sony FX9 50mm prime, f/2.8.
```

### Cutaway C — public URL on phone screen (3 s)

```
Photorealistic close-up of a modern smartphone (iPhone 15 Pro,
matte titanium) held vertically on a clean walnut desk. The screen
shows a Safari mobile browser opened to a chatbot widget — bottom
right corner has a small blue circular launcher button visible.
The address bar at the top shows "your-app.fly.dev". Soft natural
window light from the upper left, subtle reflections on the glass,
sharp focus on the screen. No people, no hands holding the phone.
Sony FX9, 50mm prime, f/2.8, photorealistic, natural skin texture
of materials, no 3D no cartoon no VFX.
```

---

## Asset checklist before recording

- [ ] Server running locally on `http://127.0.0.1:8990` with `ANTHROPIC_API_KEY` set
- [ ] `python scripts/seed_knowledge_base.py` run so KB has 10 docs / 36 chunks
- [ ] Browser zoom at 100%, viewport 1440×900 (Chrome DevTools → Custom)
- [ ] Quit unrelated apps to keep menu bar clean
- [ ] Use **Cleanshot X** or **QuickTime** for screen recording at 60 fps
- [ ] Record cursor — but disable any "click highlight" overlay (looks AI-cringe)

## Post-production in CapCut

1. Drop the 5 SR clips on V1, the 3 BR cutaways on V2
2. Mute all clip audio
3. Add VO MP3 on A1, music on A2 (-22 dB) — try
   ["Awakening" by Yehezkel Raz on Artlist](https://artlist.io/) or
   any minimal piano/strings underscore
4. Auto-captions ON, font: Inter Bold 36 px, drop shadow, top-center
5. Export 1080×1920 (vertical for TikTok/Reels) AND 1920×1080 (landscape for the Upwork gallery)

## Where to use the final video

| Length | Where | Aspect |
|---|---|---|
| Full 90 s | Upwork portfolio gallery, project detail page, README hero embed | 16:9 |
| 30 s cut (beats 1+2+4) | LinkedIn post, Twitter, Telegram channel pitch | 1:1 or 16:9 |
| 60 s cut (no beat 5) | TikTok/Reels for outreach to small business owners | 9:16 |

## Cost rough estimate

- 3 Higgsfield cutaways × 5 s × `seedance_2_0 fast 720p` (17.5 cr each) = **~53 credits**
- ElevenLabs Multilingual v2 voice gen for ~150 words = **~$0.20**
- CapCut: free
- **Total per video: under $5 + 1 hour of editing time**
