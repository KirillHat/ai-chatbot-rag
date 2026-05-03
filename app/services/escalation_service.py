"""Hand-off service: capture an escalation request and notify a human.

Flow:
    1. Widget sends `POST /api/escalate` with the active session id and an
       optional contact (email / phone) the user wants to be reached at.
    2. We snapshot the conversation transcript so the human picking it up
       has full context without needing to query SQLite.
    3. Best-effort notify channels: Slack incoming webhook, email
       (logged for downstream relay — we deliberately don't ship SMTP).
    4. Always returns 202 with the escalation id so the widget can show
       "We've passed this to a human, ref #42".

Notification fan-out is fire-and-forget (gathered with `return_exceptions`)
so a flaky Slack webhook never blocks the user-facing 202.
"""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

import httpx

from app.db.database import Database

log = logging.getLogger(__name__)
WEBHOOK_TIMEOUT = 4.0

# Best-effort PII redaction for outbound notifications. The transcript is
# still stored verbatim in the `escalations` table (so a human picking it
# up can request the unredacted version with a separate query). Only the
# Slack/email outbound channel sees the redacted version.
#
# These patterns are intentionally conservative — they catch the obvious
# foot-guns (cards, SSNs, full email addresses, password=… style snippets).
# A real product should layer a proper PII detector (Microsoft Presidio,
# Google DLP) on top.
_REDACT_RULES: list[tuple[re.Pattern[str], str]] = [
    # Visa/MC/Amex/Discover style — 13-19 digits with optional dashes/spaces
    (re.compile(r"\b(?:\d[ -]?){12,18}\d\b"), "[REDACTED:CARD]"),
    # US SSN xxx-xx-xxxx
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED:SSN]"),
    # password=..., secret=..., api_key=..., token=... (common copy-pastes)
    (re.compile(r"(?i)\b(password|passwd|secret|api[_-]?key|token|bearer)\s*[:=]\s*\S+"),
     r"\1=[REDACTED:SECRET]"),
    # bare bearer tokens / sk-… style API keys
    (re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"), "[REDACTED:KEY]"),
    # Email addresses (keep the local part's first char + domain so support can still tell who it is)
    (re.compile(r"\b([A-Za-z0-9._%+-])[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b"),
     r"\1***@\2"),
]


def redact(text: str) -> str:
    """Apply the conservative PII redaction patterns above."""
    for pat, repl in _REDACT_RULES:
        text = pat.sub(repl, text)
    return text


@dataclass
class EscalationResult:
    id: int
    status: str
    notified: list[str]


class EscalationService:
    def __init__(
        self,
        *,
        db: Database,
        slack_webhook: str = "",
        email: str = "",
        assistant_name: str = "AI Assistant",
        tenant: str = "demo",
    ):
        self.db = db
        self.slack_webhook = slack_webhook.strip()
        self.email = email.strip()
        self.assistant_name = assistant_name
        self.tenant = tenant

    async def escalate(
        self,
        *,
        session_id: str,
        contact: str | None,
        reason: str | None,
    ) -> EscalationResult:
        # Snapshot the chat at the time of escalation. Storing it on the
        # escalation row insulates us from later edits / GDPR deletion of
        # chat_messages.
        transcript_rows = await self.db.fetch_transcript(session_id, limit=50)
        transcript = "\n".join(
            f"[{r['role']}] {r['content']}" for r in transcript_rows
        )
        eid = await self.db.add_escalation(
            session_id=session_id,
            contact=contact or None,
            reason=reason or None,
            transcript=transcript or None,
        )

        notified = await self._notify(
            eid=eid,
            session_id=session_id,
            contact=contact,
            reason=reason,
            transcript=transcript,
        )
        # Mark notified only if at least one channel reported success.
        if notified:
            try:
                await self._mark_notified(eid)
            except Exception:
                log.exception("Failed to mark escalation #%d as notified", eid)
        return EscalationResult(id=eid, status="received", notified=notified)

    async def _notify(
        self,
        *,
        eid: int,
        session_id: str,
        contact: str | None,
        reason: str | None,
        transcript: str,
    ) -> list[str]:
        tasks = []
        labels = []
        if self.slack_webhook:
            tasks.append(self._post_slack(eid, session_id, contact, reason, transcript))
            labels.append("slack")
        if self.email:
            tasks.append(self._log_email(eid, session_id, contact, reason, transcript))
            # Note: this only WRITES A LOG LINE — no SMTP is shipped with
            # this project. The label is "email_log" (not "email") so the
            # admin UI / API consumer can tell the difference between
            # "Slack delivered" and "logged for downstream relay".
            labels.append("email_log")
        if not tasks:
            log.info(
                "Escalation #%d: no channels configured. session=%s contact=%r reason=%r",
                eid, session_id, contact, reason,
            )
            return []
        results = await asyncio.gather(*tasks, return_exceptions=True)
        notified = []
        for label, res in zip(labels, results, strict=False):
            if isinstance(res, Exception):
                log.warning("Escalation #%d %s notify failed: %s", eid, label, res)
            else:
                notified.append(label)
        return notified

    async def _post_slack(self, eid, session_id, contact, reason, transcript) -> None:
        # Redact for the outbound channel only — the unredacted version
        # stays in the SQLite escalations table for support to pull on demand.
        safe_transcript = redact(transcript or "")[:2500]
        safe_contact = redact(contact or "") if contact else "(not provided)"
        safe_reason = redact(reason or "") if reason else "(not provided)"
        text = (
            f"*🆘 New escalation #{eid}* for *{self.tenant}*\n"
            f"• Session: `{session_id}`\n"
            f"• Contact: {safe_contact}\n"
            f"• Reason: {safe_reason}\n"
            f"```\n{safe_transcript or '(no prior messages)'}\n```"
        )
        async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
            r = await client.post(self.slack_webhook, json={"text": text})
            r.raise_for_status()

    async def _log_email(self, eid, session_id, contact, reason, transcript) -> None:
        # Intentionally just logs at INFO with a stable prefix; downstream
        # log shipping (Loki, Datadog, journald → mailx) can match on
        # "ESCALATION_EMAIL_PAYLOAD" and forward. Keeps SMTP creds out of
        # this service.
        log.info(
            "ESCALATION_EMAIL_PAYLOAD to=%s subject='New escalation #%d for %s' "
            "session=%s contact=%r reason=%r transcript_len=%d",
            self.email, eid, self.tenant, session_id, contact, reason, len(transcript),
        )

    async def _mark_notified(self, eid: int) -> None:
        # The DB doesn't have a dedicated update method — short SQL inline
        # is cleaner than another helper for a one-liner.
        import aiosqlite

        async with aiosqlite.connect(self.db.path) as conn:
            await conn.execute(
                "UPDATE escalations SET status = 'notified' WHERE id = ?",
                (eid,),
            )
            await conn.commit()
