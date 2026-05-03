# Chat Widget — Embed Guide

A vanilla-JS embeddable widget. **Zero dependencies, ~28 KB raw (~9 KB gzipped), no build step.**
Works on any HTML page that can include a `<script>` tag.

## Quick start

Add this one tag right before `</body>`:

```html
<script src="https://your-host.com/widget/chat-widget.js" defer></script>
```

That's it. The widget appears as a chat button in the bottom-right corner.
On click it expands into a panel that talks to your `/api/chat` endpoint.

## Configuration via `data-*` attributes

```html
<script src="https://your-host.com/widget/chat-widget.js"
        data-api="https://your-host.com"
        data-name="Concierge Bot"
        data-greeting="Welcome to Hotel Aurora! How can I help?"
        data-primary="#A1845C"
        data-tenant="hotel-aurora"
        data-open="false"
        defer></script>
```

| Attribute        | Default                                | Notes                                                  |
| ---------------- | -------------------------------------- | ------------------------------------------------------ |
| `data-api`       | `window.location.origin`               | API base URL — useful when the widget is on `acme.com` and the bot lives on `bot.acme.com`. |
| `data-name`      | from `/api/widget/config`              | Header title.                                          |
| `data-greeting`  | from `/api/widget/config`              | First message shown when the panel opens.              |
| `data-primary`   | from `/api/widget/config`              | Brand color — used for the launcher, header, user bubbles, send button, focus ring. |
| `data-tenant`    | `default`                              | Used as the `localStorage` key for the conversation id. Use a unique value per site. |
| `data-open`      | `false`                                | Set `"true"` to auto-open the panel on page load.      |
| `data-streaming` | `true`                                 | When `true`, hits `POST /api/chat/stream` for token-by-token responses. Falls back to the blocking `POST /api/chat` if the stream fails before the first token (most often a buffering proxy). Set to `"false"` to skip the streaming attempt entirely on hosts where you know the proxy buffers SSE — see "Streaming behind a reverse proxy" below. |

Server-side defaults come from `/api/widget/config` (driven by `.env` →
`ASSISTANT_NAME`, etc.). `data-*` attributes always win.

## "Talk to a human" — hand-off

The widget's footer has a "Talk to a human" button that opens a small
form (contact + reason). On submit it `POST`s to `/api/escalate` with
the active session id; the backend captures the conversation transcript
and notifies whichever channels are configured server-side (Slack
incoming-webhook via `ESCALATION_SLACK_WEBHOOK`, or just an INFO log
line tagged `ESCALATION_EMAIL_PAYLOAD` for downstream relay if
`ESCALATION_EMAIL` is set).

Notes:

- The button is disabled while a chat response is in flight (so a
  mid-stream click can't interleave with the streaming bubble).
- A new visitor must send at least one message before the form will
  submit — there's no session id to attach the escalation to otherwise.
- The contact field accepts an email (`alice@example.com`) or a phone
  number (`+1 555 0123`) — anything else is rejected client-side. Empty
  contact is allowed if you'd rather follow up via the existing chat
  thread alone.
- Outbound transcripts to Slack go through a conservative PII redactor
  (cards, SSNs, `password=…`-style snippets, email local-parts) — the
  unredacted version is kept in the `escalations` table for support to
  pull via direct DB query.

## Streaming behind a reverse proxy

The `/api/chat/stream` SSE endpoint sends `Cache-Control: no-cache,
no-transform` and `X-Accel-Buffering: no` headers, which most modern
proxies honour. If you see token-by-token rendering work locally but
not in production, your proxy is buffering. The fixes:

- **nginx**: in your `location` block — `proxy_buffering off;
  proxy_cache off; chunked_transfer_encoding on;`
- **Cloudflare**: streaming works on free/paid plans for `text/event-stream`,
  but the "Always Use HTTPS" + auto-minify combo can occasionally rewrite
  the response. Set "Cache rules" to bypass for `/api/chat/stream`.
- **Apache**: ensure `mod_proxy_http` is current; `SetEnv proxy-sendchunked 1`.
- **As a last resort**: set `data-streaming="false"` on the widget tag.
  The widget will use the blocking `POST /api/chat` endpoint instead.

## Browser support

Modern evergreen browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+).
Uses `fetch`, `localStorage`, `requestAnimationFrame` — all available without
polyfills. No transpilation needed; the file is ES2017 vanilla.

## Privacy / cross-origin

- The widget never touches `document.cookie` and never reads from other tabs.
- The only thing it persists is a 32-character session id in `localStorage`,
  used so a returning visitor sees a continuous conversation. Clearing site
  data forgets it.
- Configure `CORS_ORIGINS` on the server to allow only the domains you embed
  on. `*` is fine for the public demo, **never** for a customer install.

## Theming

For deeper visual changes, override the CSS after the widget loads:

```html
<style>
  .aicw-launcher { width: 56px !important; height: 56px !important; }
  .aicw-panel    { border-radius: 8px !important; }
  .aicw-header   { background: linear-gradient(135deg,#0F62FE,#0043CE) !important; }
</style>
```

All widget classes are prefixed with `aicw-` so they don't clash with the host
page.

## Mobile

Below 480 px the panel expands to fill nearly the whole viewport. The
launcher stays in the bottom-right corner with a smaller offset.

## How it talks to the backend

```
POST /api/chat
Content-Type: application/json

{
  "message": "What time is breakfast?",
  "history": [{"role":"user","content":"…"}, {"role":"assistant","content":"…"}],
  "session_id": "abc123…" | null
}
```

Response:

```json
{
  "answer": "Breakfast is served 07:00–10:30 in the Aurora dining room [1].",
  "citations": [
    {
      "document_id": 1,
      "document_name": "hotel_info.md",
      "snippet": "Breakfast is served daily from 07:00 to 10:30…",
      "score": 0.84
    }
  ],
  "session_id": "abc123…",
  "used_documents": 2
}
```

The widget renders `[1]` as a clickable chip at the bottom of the answer; on
click it expands to show the document name and a 280-character snippet.
