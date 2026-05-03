# Screenshots

This folder is the home for marketing visuals (cover image, demo gif,
gallery) used in the README and on the Upwork portfolio listing.

It's intentionally empty in the repo — pixel-perfect screenshots are best
captured against a deployed instance, not generated. Capture them with:

1. **Boot the demo:**
   ```bash
   uvicorn app.main:app --reload
   python scripts/seed_knowledge_base.py
   ```

2. **Or just run the capture script** — `python scripts/capture_screenshots.py`
   produces all 8 shots through Playwright in ~20 seconds. The list:
   - `01_hotel_landing.png`        — hotel page, chat closed
   - `02_hotel_widget_open.png`    — same page, widget open with greeting
   - `03_hotel_chat_with_answer.png` — Q&A flow with citation chip expanded
   - `04_law_landing.png`          — law-firm page, chat closed
   - `05_law_widget_open.png`      — law-firm chat, brand-blue
   - `06_admin_empty.png`          — admin login screen pre-connect
   - `07_admin_with_docs.png`      — admin after the demo KB was seeded
   - `08_admin_analytics.png`      — analytics tab populated

   **Manual capture** (if Playwright isn't installed): open each URL in a
   1440×900 browser, take screenshots, name them with the IDs above.

3. **Make the cover** (`cover.png`):
   - 1600×900, two halves: hotel landing on the left, law-firm landing on the right, both with the widget open showing a cited answer.

4. **Make the demo GIF** (`demo.gif`):
   - 30-45 s, 800 px wide, ≤8 fps via `ffmpeg`:
     ```bash
     ffmpeg -i screencast.mov -vf "fps=8,scale=800:-1:flags=lanczos" -loop 0 demo.gif
     ```

## Suggested gallery order on Upwork

1. `cover.png`
2. `02_widget_open_hotel.png` — the cited answer is the killer screenshot
3. `05_admin_uploading.png` — proves the "PDF → bot learns" claim
4. `03_widget_open_law.png` — proves the "one stack, multiple verticals" claim
5. `04_admin_empty.png` — admin UX
6. `06_architecture.png` — the stack diagram (export from `README.md`)

## Why these screenshots are not committed

- They get out of date the moment the UI changes.
- Anyone evaluating this repo can spin up the demo in 60 seconds.
- A live demo URL (deployed once and kept on GitHub Pages or Fly.io) beats
  static screenshots in a portfolio context.
