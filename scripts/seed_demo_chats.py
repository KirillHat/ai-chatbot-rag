"""Seed realistic demo chat history so the admin analytics tab looks
production-y in screenshots / live demos.

Why this exists:
    Out of the box the analytics view shows whatever you typed during
    smoke tests — "hi", "test", and 100% no-answer rate because there
    was no Anthropic API key wired up. That makes a terrible portfolio
    screenshot. This script wipes `chat_sessions` + `chat_messages`,
    then inserts ~15 realistic Q&A pairs spread across the last 7 days,
    plus a handful of "no-answer" replies (for a believable ~10-15%
    no-answer rate) and 3 escalations.

Run BEFORE re-running `scripts/capture_screenshots.py` for portfolio
shots. Safe to re-run — fully resets the chat log.
"""

from __future__ import annotations

import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiosqlite

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402

# (question, assistant answer, citation doc, is_no_answer)
HOTEL_TURNS = [
    ("What time is breakfast served?",
     "Breakfast is served daily from 07:00 to 10:30 in the Aurora dining "
     "room (08:00–11:00 on Sundays and bank holidays). Hot Mediterranean "
     "buffet with espresso, eggs to order, and gluten-free / vegan "
     "options on request [1].", "03_amenities.md", False),
    ("Do you have rooms with a sea view?",
     "Yes — our Deluxe Sea View rooms (28 m², from €210/night) face the "
     "Mediterranean with a balcony and freestanding soaking tub. The "
     "Terrace Suite (62 m², from €420/night) has a private rooftop with "
     "an outdoor tub overlooking the harbour [1].", "02_rooms_and_rates.md", False),
    ("How much is parking?",
     "Underground valet parking is €18 per night, payable at check-out. "
     "The garage has 12 spaces — it's worth booking when you make the "
     "reservation. Two EV chargers (Type 2, 22 kW) are free for guests [1].",
     "03_amenities.md", False),
    ("Can I check in early?",
     "Standard check-in is from 15:00, but early check-in from 12:00 is "
     "usually possible for an extra €25, subject to availability [1]. "
     "If you'd like, I can flag your arrival time so the front desk can "
     "try to have your room ready.", "01_general.md", False),
    ("What's the cancellation policy?",
     "Free cancellation up to 48 hours before arrival. Within 48 hours "
     "we charge the first night; no-shows are charged for the full stay. "
     "Non-refundable rates (10% off) cannot be cancelled or modified [1].",
     "02_rooms_and_rates.md", False),
    ("Are pets allowed?",
     "Dogs up to 25 kg and cats are welcome in Classic Double and Junior "
     "Suite categories. The first pet is free, second is €15/night. "
     "We provide a bowl, blanket and a treat on arrival — please bring "
     "your own food [1].", "03_amenities.md", False),
    ("Is there a transfer from the airport?",
     "Yes — €35 one-way for up to 3 passengers, just book at least 12 "
     "hours ahead. The airport is about 15–20 minutes by taxi (~€18) [1].",
     "03_amenities.md", False),
    ("What's the best restaurant nearby?",
     "Within 200 m we always recommend Casa Lina (trattoria, pasta from "
     "€14) and Mar y Sal (seafood, tasting menu €58, closed Mondays). "
     "For a casual coffee, Caffè 12 has the best espresso on the street "
     "and opens at 06:30 [1].", "04_dining_and_neighbourhood.md", False),
    ("Do you have a pool?",
     "Yes — a 12 m heated indoor pool (28°C) plus a Finnish sauna and "
     "steam room. Open 07:00 to 22:00 daily. Towels and robes are "
     "included; the sauna is over-16 only [1].", "03_amenities.md", False),
    ("Can I rent a bicycle from the hotel?",
     "Yes — €15 per day, helmets included, paid at the front desk [1].",
     "03_amenities.md", False),
    # The two below are deliberate "I don't have" answers so the analytics
    # tab shows a realistic ~10-15% no-answer rate.
    ("Do you have a kids' club?",
     "I don't have any information about a kids' club. Hotel Aurora is a "
     "small 24-room property — would you like me to put you in touch "
     "with the reception so they can confirm what's available for "
     "children during your stay?", None, True),
    ("Can I request a Tesla as the airport pickup vehicle?",
     "I don't have that information. The reception can usually arrange a "
     "specific car type with our partner taxi service — would you like "
     "me to flag the request to them?", None, True),
]

LAW_TURNS = [
    ("How much does an NDA review cost?",
     "A standard mutual NDA review is $400 fixed (2 business days). "
     "One-way or non-standard NDAs are $500–$750 fixed. Same-day rush "
     "is sometimes possible for existing clients (+50% fee) [1].",
     "03_pricing_and_intake.md", False),
    ("Are you admitted in California?",
     "David Klein is admitted in Massachusetts and California. For "
     "California-only matters he handles them directly; for matters in "
     "other states we either work with local counsel we trust or apply "
     "for pro hac vice if it's a one-off [1].", "01_about_the_firm.md", False),
    ("Do you handle patent applications?",
     "We don't handle patent prosecution. We refer patent work to two "
     "specialty firms we've worked with for years and trust [1].",
     "02_practice_areas.md", False),
    ("What's your initial consultation?",
     "It's a paid 45-minute video call for $250. By the end we'll either "
     "quote a fixed fee for the work or tell you we're not the right "
     "fit and refer you elsewhere — never an open meter [1].",
     "03_pricing_and_intake.md", False),
    ("Can you do a Delaware C-Corp setup for a non-US founder?",
     "Yes — that's one of our most common engagements. The founder "
     "package covers incorporation, bylaws, founder stock with vesting, "
     "IP assignment and an initial board consent. $1,500 + state filing "
     "fees [1].", "03_pricing_and_intake.md", False),
]


async def seed():
    settings = get_settings()
    db_path = settings.sqlite_path
    if not db_path.exists():
        print(f"⚠ {db_path} doesn't exist — run the server once to init the DB first")
        return

    async with aiosqlite.connect(db_path) as db:
        print("Wiping chat_sessions + chat_messages + escalations…")
        await db.execute("DELETE FROM chat_messages")
        await db.execute("DELETE FROM chat_sessions")
        await db.execute("DELETE FROM escalations")
        await db.commit()

        rng = random.Random(42)
        all_turns = HOTEL_TURNS + LAW_TURNS

        # Generate ~3-5 questions per session, distributed over the last 7
        # days. Each session gets a UUID and a single user-agent string.
        now = datetime.now(timezone.utc)
        session_count = 12
        msg_count = 0
        for _s in range(session_count):
            sid = uuid.uuid4().hex
            session_age_days = rng.uniform(0.05, 6.9)
            session_started = now - timedelta(days=session_age_days)
            ua = rng.choice([
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Version/17.4 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Version/17.4 Safari/605.1.15",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Linux; Android 14) Chrome/124.0.0.0 Mobile Safari/537.36",
            ])
            await db.execute(
                "INSERT INTO chat_sessions (id, user_agent, created_at, updated_at) "
                "VALUES (?, ?, ?, ?)",
                (sid, ua, session_started.isoformat(timespec="seconds"),
                 session_started.isoformat(timespec="seconds")),
            )

            n_turns = rng.randint(2, 5)
            picks = rng.sample(all_turns, n_turns)
            t = session_started
            for q, a, doc, _is_no in picks:
                t = t + timedelta(seconds=rng.randint(20, 180))
                await db.execute(
                    "INSERT INTO chat_messages (session_id, role, content, created_at) "
                    "VALUES (?, 'user', ?, ?)",
                    (sid, q, t.isoformat(timespec="seconds")),
                )
                t = t + timedelta(seconds=rng.randint(2, 8))
                cit = (
                    f'[{{"document_id":1,"document_name":"{doc}",'
                    f'"snippet":"…","score":0.82}}]'
                ) if doc else None
                await db.execute(
                    "INSERT INTO chat_messages "
                    "(session_id, role, content, citations, created_at) "
                    "VALUES (?, 'assistant', ?, ?, ?)",
                    (sid, a, cit, t.isoformat(timespec="seconds")),
                )
                msg_count += 2

        # 3 escalations — 2 notified (slack), 1 still pending.
        for sid_age, contact, reason, status in [
            (0.5, "anna@example.com", "Need a quote for a 2-week stay (12 guests)", "notified"),
            (2.1, "+1 555 0142",     "Question about deposit refund timing",        "notified"),
            (0.2, None,              "Discuss accessible room options",              "pending"),
        ]:
            sid = uuid.uuid4().hex
            t = now - timedelta(days=sid_age)
            await db.execute(
                "INSERT INTO escalations "
                "(session_id, contact, reason, transcript, status, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (sid, contact, reason, "[user] " + reason, status,
                 t.isoformat(timespec="seconds")),
            )

        await db.commit()

    # Sanity-print
    async with aiosqlite.connect(db_path) as db:
        cur = await db.execute("SELECT COUNT(*) FROM chat_sessions")
        sessions = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM chat_messages")
        messages = (await cur.fetchone())[0]
        cur = await db.execute("SELECT COUNT(*) FROM escalations")
        escs = (await cur.fetchone())[0]

    print(
        f"\n✓ Seeded: {sessions} sessions / {messages} messages "
        f"/ {escs} escalations across the last 7 days"
    )


if __name__ == "__main__":
    asyncio.run(seed())
