"""Capture portfolio screenshots from the running demo via Playwright.

Captures eight images that cover the three things a Upwork client wants
to see at a glance:

  01_hotel_landing.png          — the hotel page (chat closed, hero in view)
  02_hotel_widget_open.png      — same page, widget panel open with greeting
  03_hotel_chat_with_answer.png — Q&A flow with citation chip expanded
  04_law_landing.png            — the law-firm page (chat closed)
  05_law_widget_open.png        — law-firm chat with a different brand colour
  06_admin_empty.png            — admin login screen, before any token entered
  07_admin_with_docs.png        — admin panel after the demo KB was seeded
  08_admin_analytics.png        — analytics tab populated

Prerequisites:
  - The server is running locally on the URL passed via --url (default
    http://127.0.0.1:8990).
  - The KB is seeded so admin shows non-zero counts:
      python scripts/seed_knowledge_base.py
  - Playwright is installed (intentionally NOT in requirements.txt to
    keep the runtime image small):
      pip install playwright && playwright install chromium

Usage:
  python scripts/capture_screenshots.py
  python scripts/capture_screenshots.py --url https://your-deploy.example.com
  python scripts/capture_screenshots.py --token MY_ADMIN_TOKEN
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "screenshots"


async def _inject_mock_answer(page, question: str, answer_text: str, citation: dict) -> None:
    """Make the widget LOOK like it just got a streamed answer, without
    actually hitting the backend. Used when ANTHROPIC_API_KEY isn't
    available at capture time — produces portfolio-grade screenshots
    that match what the live demo will actually show."""
    await page.fill(".aicw-input", question)
    # Render the user bubble through the widget's own append helper so the
    # DOM/styles match exactly what `onSend()` would produce.
    await page.evaluate(
        """({question, answer, citation}) => {
            const body = document.querySelector(".aicw-body");
            const u = document.createElement("div");
            u.className = "aicw-msg user";
            u.textContent = question;
            body.appendChild(u);
            const b = document.createElement("div");
            b.className = "aicw-msg bot";
            b.textContent = answer;
            body.appendChild(b);
            // Mock citation chip + expanded detail card (same DOM as the real path)
            const cw = document.createElement("div");
            cw.className = "aicw-citations";
            const chip = document.createElement("button");
            chip.className = "aicw-cite";
            chip.disabled = true;
            chip.style.opacity = "0.55";
            chip.textContent = `[1] ${citation.document_name}`;
            cw.appendChild(chip);
            body.appendChild(cw);
            const detail = document.createElement("div");
            detail.className = "aicw-cite-detail";
            const name = document.createElement("span");
            name.className = "aicw-cite-name";
            name.textContent = `[1] ${citation.document_name}`;
            const snip = document.createElement("span");
            snip.textContent = citation.snippet;
            detail.appendChild(name);
            detail.appendChild(snip);
            body.appendChild(detail);
            body.scrollTop = body.scrollHeight;
            document.querySelector(".aicw-input").value = "";
        }""",
        {"question": question, "answer": answer_text, "citation": citation},
    )
    await page.wait_for_timeout(400)


async def capture(url: str, token: str, mock: bool = False) -> None:
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print(
            "Playwright is not installed. Run:\n"
            "    pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        sys.exit(2)

    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        ctx = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,  # @2x for crisper portfolio shots
        )

        # ---- Hotel ----
        page = await ctx.new_page()
        await page.goto(f"{url}/demo/hotel/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(OUT / "01_hotel_landing.png"))

        await page.click(".aicw-launcher")
        await page.wait_for_selector(".aicw-panel", state="visible")
        # Tiny pause for the open animation
        await page.wait_for_timeout(300)
        await page.screenshot(path=str(OUT / "02_hotel_widget_open.png"))

        # Mid-conversation shot. With ANTHROPIC_API_KEY set we hit the real
        # endpoint; without it we inject a representative answer so the
        # screenshot still looks production-realistic.
        if mock:
            await _inject_mock_answer(
                page,
                question="What time is breakfast served?",
                answer_text=(
                    "Breakfast is served daily from 07:00 to 10:30 in the "
                    "Aurora dining room (08:00–11:00 on Sundays and bank "
                    "holidays). It's a hot Mediterranean buffet with eggs "
                    "cooked to order, locally-roasted espresso, and "
                    "vegan/gluten-free options on request [1]."
                ),
                citation={
                    "document_name": "03_amenities.md",
                    "snippet": (
                        "Breakfast — Hours: 07:00 – 10:30 daily, "
                        "08:00 – 11:00 on Sundays and bank holidays. "
                        "Where: Aurora dining room, ground floor. "
                        "Style: hot Mediterranean buffet — eggs cooked to "
                        "order, charcuterie, cheeses, fresh fruit, pastries…"
                    ),
                },
            )
        else:
            await page.fill(".aicw-input", "What time is breakfast?")
            await page.click(".aicw-send")
            with contextlib.suppress(Exception):
                await page.wait_for_selector(".aicw-typing", state="detached", timeout=15000)
            chips = await page.query_selector_all(".aicw-cite")
            if chips:
                await chips[0].click()
                await page.wait_for_timeout(200)
        await page.screenshot(path=str(OUT / "03_hotel_chat_with_answer.png"))
        await page.close()

        # ---- Law firm ----
        page = await ctx.new_page()
        await page.goto(f"{url}/demo/law/")
        await page.wait_for_load_state("networkidle")
        await page.screenshot(path=str(OUT / "04_law_landing.png"))
        await page.click(".aicw-launcher")
        await page.wait_for_selector(".aicw-panel", state="visible")
        await page.wait_for_timeout(300)
        if mock:
            await _inject_mock_answer(
                page,
                question="How much does an NDA review cost?",
                answer_text=(
                    "A standard mutual NDA review is a $400 fixed fee, "
                    "typically turned around in 2 business days. One-way "
                    "or non-standard NDAs are quoted between $500 – $750 "
                    "fixed [1]. For anything case-specific I'll connect "
                    "you with one of our attorneys."
                ),
                citation={
                    "document_name": "03_pricing_and_intake.md",
                    "snippet": (
                        "NDA review — standard mutual: $400 fixed. "
                        "NDA review — one-way / non-standard: $500 – $750 "
                        "fixed. Standard turnaround: 2 business days. "
                        "Same-day rush is sometimes possible for existing "
                        "clients (+50% on the fee)."
                    ),
                },
            )
        await page.screenshot(path=str(OUT / "05_law_widget_open.png"))
        await page.close()

        # ---- Admin ----
        page = await ctx.new_page()
        await page.goto(f"{url}/demo/admin/")
        await page.wait_for_load_state("networkidle")
        # 06: pre-connect state — login screen, both other panels hidden.
        await page.screenshot(path=str(OUT / "06_admin_empty.png"))
        # Connect — reveals the upload + analytics + docs panels.
        await page.fill("#token", token)
        await page.click("#connect-btn")
        await page.wait_for_selector("#upload-panel", state="visible", timeout=10000)
        await page.wait_for_timeout(500)  # let analytics paint
        # 07: full admin after connect.
        await page.screenshot(path=str(OUT / "07_admin_with_docs.png"), full_page=True)

        # Scroll to analytics for a focused screenshot.
        await page.evaluate(
            "document.getElementById('analytics-panel').scrollIntoView({block: 'start'})"
        )
        await page.wait_for_timeout(300)
        await page.screenshot(path=str(OUT / "08_admin_analytics.png"))

        await page.close()
        await browser.close()

    print(f"\n✓ Wrote {len(list(OUT.glob('*.png')))} screenshots to {OUT}/")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default="http://127.0.0.1:8990",
                    help="Base URL of the running server")
    ap.add_argument("--token", default="demo-please-do-not-abuse-1234567890",
                    help="ADMIN_API_TOKEN for the admin captures")
    ap.add_argument("--mock", action="store_true",
                    help="Inject a representative Q&A into shots #3 and #5 "
                         "instead of hitting /api/chat. Useful when "
                         "ANTHROPIC_API_KEY isn't set at capture time.")
    args = ap.parse_args()
    asyncio.run(capture(args.url.rstrip("/"), args.token, mock=args.mock))


if __name__ == "__main__":
    main()
