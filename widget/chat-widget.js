/**
 * AI Chatbot Widget — embeddable, zero dependencies.
 *
 * Embed in any HTML page:
 *   <script src="https://your-host/widget/chat-widget.js"
 *           data-api="https://your-host"
 *           data-name="AI Assistant"
 *           defer></script>
 *
 * The script tag's data-* attributes override what /api/widget/config
 * returns, so you can rebrand the widget per page without touching the
 * server.
 */
(function () {
  "use strict";

  if (window.__aiChatWidgetLoaded) return;
  window.__aiChatWidgetLoaded = true;

  const SCRIPT = document.currentScript || (function () {
    const all = document.getElementsByTagName("script");
    return all[all.length - 1];
  })();

  const API_BASE = (SCRIPT.dataset.api || window.location.origin).replace(/\/$/, "");
  const OVERRIDE_NAME = SCRIPT.dataset.name;
  const OVERRIDE_GREETING = SCRIPT.dataset.greeting;
  const OVERRIDE_PRIMARY = SCRIPT.dataset.primary;
  const OPEN_BY_DEFAULT = SCRIPT.dataset.open === "true";
  // Streaming on by default; opt-out per-tenant via data-streaming="false"
  // (handy when the host is behind a proxy that buffers SSE).
  const STREAMING = SCRIPT.dataset.streaming !== "false";
  const STORAGE_KEY = "aiChatSessionId__" + (SCRIPT.dataset.tenant || "default");

  const HISTORY_LIMIT = 10;

  // --- State -------------------------------------------------------------

  const state = {
    config: {
      name: "AI Assistant",
      greeting: "Hi! Ask me anything.",
      placeholder: "Type your question…",
      poweredBy: "Claude · RAG",
      theme: {
        primary: "#0F62FE",
        background: "#FFFFFF",
        userBubble: "#0F62FE",
        botBubble: "#F2F4F8",
      },
    },
    history: [],
    sessionId: localStorage.getItem(STORAGE_KEY) || null,
    open: false,
    busy: false,
  };

  // --- Styles ------------------------------------------------------------

  function injectStyles(theme) {
    if (document.getElementById("ai-chat-widget-styles")) return;
    const css = `
      .aicw-launcher{position:fixed;bottom:24px;right:24px;width:60px;height:60px;border-radius:50%;background:${theme.primary};color:#fff;border:none;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.18);display:flex;align-items:center;justify-content:center;z-index:2147483646;transition:transform .18s ease,box-shadow .18s ease;font-family:inherit}
      .aicw-launcher:hover{transform:translateY(-2px);box-shadow:0 12px 28px rgba(0,0,0,.22)}
      .aicw-launcher svg{width:28px;height:28px}
      .aicw-panel{position:fixed;bottom:96px;right:24px;width:380px;max-width:calc(100vw - 32px);height:560px;max-height:calc(100vh - 120px);background:${theme.background};border-radius:16px;box-shadow:0 20px 60px rgba(0,0,0,.22);display:flex;flex-direction:column;overflow:hidden;z-index:2147483647;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#161616;animation:aicw-pop .18s ease}
      @keyframes aicw-pop{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}
      .aicw-header{background:${theme.primary};color:#fff;padding:14px 16px;display:flex;align-items:center;gap:12px;flex-shrink:0}
      .aicw-avatar{width:36px;height:36px;border-radius:50%;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;font-weight:700;font-size:15px;letter-spacing:-.02em}
      .aicw-title{font-weight:600;font-size:15px;line-height:1.2}
      .aicw-sub{font-size:11px;opacity:.85;margin-top:2px}
      .aicw-close{margin-left:auto;background:transparent;border:none;color:#fff;cursor:pointer;width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;opacity:.85}
      .aicw-close:hover{background:rgba(255,255,255,.15);opacity:1}
      .aicw-body{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;background:#FAFAFC;scroll-behavior:smooth}
      .aicw-msg{max-width:88%;padding:10px 14px;border-radius:14px;font-size:14px;line-height:1.5;word-wrap:break-word;white-space:pre-wrap;animation:aicw-fade .15s ease}
      @keyframes aicw-fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
      .aicw-msg.user{background:${theme.userBubble};color:#fff;align-self:flex-end;border-bottom-right-radius:4px}
      .aicw-msg.bot{background:${theme.botBubble};color:#161616;align-self:flex-start;border-bottom-left-radius:4px}
      .aicw-msg.error{background:#FEE;color:#A1240B;align-self:flex-start;border-bottom-left-radius:4px}
      .aicw-msg a{color:${theme.primary};text-decoration:underline}
      .aicw-citations{display:flex;flex-wrap:wrap;gap:6px;margin-top:6px;align-self:flex-start;max-width:88%}
      .aicw-cite{font-size:11px;color:#525252;background:#fff;border:1px solid #E0E0E0;padding:4px 8px;border-radius:8px;cursor:pointer;transition:background .15s}
      .aicw-cite:hover{background:#F2F4F8}
      .aicw-cite-detail{font-size:11.5px;color:#393939;background:#fff;border:1px solid #E0E0E0;border-left:3px solid ${theme.primary};padding:8px 10px;border-radius:8px;align-self:flex-start;max-width:88%;line-height:1.45}
      .aicw-cite-detail .aicw-cite-name{font-weight:600;color:#161616;display:block;margin-bottom:4px}
      .aicw-typing{display:inline-flex;gap:4px;padding:14px;align-self:flex-start;background:${theme.botBubble};border-radius:14px;border-bottom-left-radius:4px}
      .aicw-typing span{width:7px;height:7px;border-radius:50%;background:#8D8D8D;animation:aicw-blink 1.2s infinite}
      .aicw-typing span:nth-child(2){animation-delay:.18s}
      .aicw-typing span:nth-child(3){animation-delay:.36s}
      @keyframes aicw-blink{0%,80%,100%{opacity:.3;transform:translateY(0)}40%{opacity:1;transform:translateY(-2px)}}
      .aicw-input-row{display:flex;gap:8px;padding:12px;border-top:1px solid #E0E0E0;background:${theme.background};flex-shrink:0}
      .aicw-input{flex:1;border:1px solid #C6C6C6;border-radius:10px;padding:10px 12px;font-size:14px;font-family:inherit;outline:none;background:#fff;color:#161616;resize:none;max-height:120px;line-height:1.4}
      .aicw-input:focus{border-color:${theme.primary};box-shadow:0 0 0 3px ${theme.primary}22}
      .aicw-send{background:${theme.primary};color:#fff;border:none;border-radius:10px;width:42px;height:42px;display:flex;align-items:center;justify-content:center;cursor:pointer;transition:opacity .15s}
      .aicw-send:disabled{opacity:.45;cursor:not-allowed}
      .aicw-send svg{width:18px;height:18px}
      .aicw-footer{padding:8px 12px 10px;text-align:center;font-size:10.5px;color:#8D8D8D;background:${theme.background};display:flex;align-items:center;justify-content:space-between;gap:10px;border-top:1px solid ${theme.botBubble}}
      .aicw-footer a,.aicw-handoff{color:#525252;text-decoration:none;background:none;border:none;padding:2px 4px;cursor:pointer;font:inherit;font-size:11px}
      .aicw-handoff:hover{color:${theme.primary};text-decoration:underline}
      .aicw-handoff svg{width:11px;height:11px;vertical-align:-1px;margin-right:3px}
      .aicw-handoff-form{padding:14px 16px;border-top:1px solid ${theme.botBubble};background:#FAFAFC;display:none;flex-shrink:0}
      .aicw-handoff-form.show{display:block;animation:aicw-fade .18s ease}
      .aicw-handoff-form h4{margin:0 0 4px;font-size:13.5px;font-weight:600;color:#161616}
      .aicw-handoff-form p{margin:0 0 10px;font-size:12px;color:#525252}
      .aicw-handoff-form input,.aicw-handoff-form textarea{width:100%;border:1px solid #C6C6C6;border-radius:6px;padding:7px 9px;font-size:12.5px;font-family:inherit;outline:none;margin-bottom:8px;background:#fff;color:#161616;box-sizing:border-box}
      .aicw-handoff-form input:focus,.aicw-handoff-form textarea:focus{border-color:${theme.primary};box-shadow:0 0 0 2px ${theme.primary}22}
      .aicw-handoff-form textarea{resize:vertical;min-height:54px;line-height:1.4}
      .aicw-handoff-form .aicw-handoff-row{display:flex;gap:8px;align-items:center}
      .aicw-handoff-form .aicw-handoff-submit{background:${theme.primary};color:#fff;border:none;border-radius:6px;padding:7px 14px;font-size:12.5px;font-weight:500;cursor:pointer}
      .aicw-handoff-form .aicw-handoff-submit:disabled{opacity:.5;cursor:not-allowed}
      .aicw-handoff-form .aicw-handoff-cancel{background:transparent;border:none;color:#525252;font-size:12px;cursor:pointer;padding:7px 6px}
      @media (max-width:480px){.aicw-panel{right:8px;left:8px;bottom:80px;width:auto;height:75vh}.aicw-launcher{right:16px;bottom:16px}}
    `;
    const style = document.createElement("style");
    style.id = "ai-chat-widget-styles";
    style.textContent = css;
    document.head.appendChild(style);
  }

  // --- DOM building ------------------------------------------------------

  const els = {};

  function buildLauncher() {
    const btn = document.createElement("button");
    btn.className = "aicw-launcher";
    btn.setAttribute("aria-label", "Open chat");
    btn.innerHTML = `
      <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
        <path d="M12 2C6.48 2 2 6.03 2 11c0 2.49 1.13 4.74 2.95 6.37L4 22l4.7-1.49C9.78 20.83 10.86 21 12 21c5.52 0 10-4.03 10-9s-4.48-10-10-10zm-3.5 10c-.83 0-1.5-.67-1.5-1.5S7.67 9 8.5 9s1.5.67 1.5 1.5S9.33 12 8.5 12zm3.5 0c-.83 0-1.5-.67-1.5-1.5S11.17 9 12 9s1.5.67 1.5 1.5S12.83 12 12 12zm3.5 0c-.83 0-1.5-.67-1.5-1.5S14.67 9 15.5 9s1.5.67 1.5 1.5-.67 1.5-1.5 1.5z"/>
      </svg>`;
    btn.addEventListener("click", togglePanel);
    document.body.appendChild(btn);
    els.launcher = btn;
  }

  function buildPanel() {
    const panel = document.createElement("div");
    panel.className = "aicw-panel";
    panel.style.display = "none";
    panel.setAttribute("role", "dialog");
    panel.setAttribute("aria-label", state.config.name);

    const initial = (state.config.name || "AI").trim().charAt(0).toUpperCase() || "A";
    panel.innerHTML = `
      <div class="aicw-header">
        <div class="aicw-avatar">${escapeHtml(initial)}</div>
        <div>
          <div class="aicw-title"></div>
          <div class="aicw-sub">Online</div>
        </div>
        <button class="aicw-close" aria-label="Close chat">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor">
            <path d="M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
      </div>
      <div class="aicw-body" aria-live="polite"></div>
      <div class="aicw-handoff-form" id="aicw-handoff-form">
        <h4>Talk to a human</h4>
        <p>Leave a contact and we'll get back to you. Your conversation will be passed along.</p>
        <input type="text" class="aicw-handoff-contact" placeholder="Email or phone (optional)"
               inputmode="email" autocomplete="email" maxlength="200" />
        <textarea class="aicw-handoff-reason" placeholder="What can we help you with? (optional)" maxlength="1000"></textarea>
        <div class="aicw-handoff-row">
          <button class="aicw-handoff-submit" type="button">Request a human</button>
          <button class="aicw-handoff-cancel" type="button">Cancel</button>
        </div>
      </div>
      <div class="aicw-input-row">
        <textarea class="aicw-input" rows="1" maxlength="2000"></textarea>
        <button class="aicw-send" aria-label="Send message">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M2.01 21 23 12 2.01 3 2 10l15 2-15 2z"/>
          </svg>
        </button>
      </div>
      <div class="aicw-footer">
        <button type="button" class="aicw-handoff" aria-label="Talk to a human"
                aria-controls="aicw-handoff-form" aria-expanded="false">
          <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>
          </svg>Talk to a human
        </button>
        <span class="aicw-poweredby"></span>
      </div>
    `;
    document.body.appendChild(panel);

    els.panel = panel;
    els.title = panel.querySelector(".aicw-title");
    els.body = panel.querySelector(".aicw-body");
    els.input = panel.querySelector(".aicw-input");
    els.send = panel.querySelector(".aicw-send");
    els.footer = panel.querySelector(".aicw-footer");

    els.title.textContent = state.config.name;
    els.input.placeholder = state.config.placeholder;
    panel.querySelector(".aicw-poweredby").textContent =
      "Powered by " + (state.config.poweredBy || "AI");

    // Hand-off form wiring.
    els.handoffForm = panel.querySelector("#aicw-handoff-form");
    els.handoffBtn = panel.querySelector(".aicw-handoff");
    els.handoffContact = panel.querySelector(".aicw-handoff-contact");
    els.handoffReason = panel.querySelector(".aicw-handoff-reason");
    els.handoffSubmit = panel.querySelector(".aicw-handoff-submit");
    els.handoffBtn.addEventListener("click", () => {
      // Hard guard: don't open while a stream is in progress; the appended
      // bot bubble would interleave with the still-streaming answer.
      if (state.busy) return;
      const isOpen = els.handoffForm.classList.toggle("show");
      els.handoffBtn.setAttribute("aria-expanded", isOpen ? "true" : "false");
      if (isOpen) {
        setTimeout(() => els.handoffContact.focus(), 50);
      }
    });
    panel.querySelector(".aicw-handoff-cancel").addEventListener("click", () => {
      els.handoffForm.classList.remove("show");
      els.handoffBtn.setAttribute("aria-expanded", "false");
      els.input.focus();
    });
    els.handoffSubmit.addEventListener("click", onHandoff);

    panel.querySelector(".aicw-close").addEventListener("click", togglePanel);
    els.send.addEventListener("click", onSend);
    els.input.addEventListener("input", autoGrow);
    els.input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        onSend();
      } else if (e.key === "Escape") {
        // Lets keyboard users (and mobile users on a software keyboard
        // that hides the close button) dismiss the panel.
        e.preventDefault();
        if (state.open) togglePanel();
      }
    });
    // Same Escape behavior when focus is anywhere inside the panel, not
    // just the input (e.g. focused on a citation chip).
    panel.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && state.open) {
        e.preventDefault();
        togglePanel();
      }
    });
  }

  // --- Rendering ---------------------------------------------------------

  function appendBubble(text, role, extraClass) {
    const div = document.createElement("div");
    div.className = "aicw-msg " + role + (extraClass ? " " + extraClass : "");
    div.textContent = text;
    els.body.appendChild(div);
    scrollToBottom();
    return div;
  }

  function appendCitations(citations) {
    if (!citations || !citations.length) return;
    const wrap = document.createElement("div");
    wrap.className = "aicw-citations";
    citations.forEach((c, i) => {
      const chip = document.createElement("button");
      chip.className = "aicw-cite";
      chip.textContent = `[${i + 1}] ${truncate(c.document_name, 32)}`;
      chip.addEventListener("click", () => {
        const detail = document.createElement("div");
        detail.className = "aicw-cite-detail";
        detail.innerHTML = `<span class="aicw-cite-name"></span><span class="aicw-cite-snip"></span>`;
        detail.querySelector(".aicw-cite-name").textContent =
          `[${i + 1}] ${c.document_name}`;
        detail.querySelector(".aicw-cite-snip").textContent = c.snippet;
        wrap.parentNode.insertBefore(detail, wrap.nextSibling);
        scrollToBottom();
        chip.disabled = true;
        chip.style.opacity = "0.55";
      });
      wrap.appendChild(chip);
    });
    els.body.appendChild(wrap);
    scrollToBottom();
  }

  function showTyping() {
    const t = document.createElement("div");
    t.className = "aicw-typing";
    t.innerHTML = "<span></span><span></span><span></span>";
    t.id = "aicw-typing-indicator";
    els.body.appendChild(t);
    scrollToBottom();
    return t;
  }

  function clearTyping() {
    const t = document.getElementById("aicw-typing-indicator");
    if (t) t.remove();
  }

  function scrollToBottom() {
    requestAnimationFrame(() => {
      els.body.scrollTop = els.body.scrollHeight;
    });
  }

  function autoGrow() {
    els.input.style.height = "auto";
    els.input.style.height = Math.min(els.input.scrollHeight, 120) + "px";
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  function truncate(s, n) {
    s = String(s || "");
    return s.length > n ? s.slice(0, n - 1) + "…" : s;
  }

  // --- Networking --------------------------------------------------------

  async function fetchConfig() {
    try {
      const res = await fetch(API_BASE + "/api/widget/config");
      if (res.ok) {
        const data = await res.json();
        state.config = Object.assign(state.config, data);
      }
    } catch (e) {
      // Stay on defaults — the backend may be local during dev.
    }
    if (OVERRIDE_NAME) state.config.name = OVERRIDE_NAME;
    if (OVERRIDE_GREETING) state.config.greeting = OVERRIDE_GREETING;
    if (OVERRIDE_PRIMARY) state.config.theme.primary = OVERRIDE_PRIMARY;
  }

  async function sendMessage(message) {
    const res = await fetch(API_BASE + "/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message: message,
        history: state.history.slice(-HISTORY_LIMIT),
        session_id: state.sessionId,
      }),
    });
    if (!res.ok) {
      let detail = "";
      try { detail = (await res.json()).detail || ""; } catch (_) {}
      const err = new Error(detail || ("HTTP " + res.status));
      err.status = res.status;
      throw err;
    }
    return await res.json();
  }

  /**
   * Stream message via SSE. Calls onEvent(eventObj) for each event:
   *   {type:"session", session_id}
   *   {type:"delta",   text}
   *   {type:"citations", citations}
   *   {type:"done",    session_id, used_documents}
   *   {type:"error",   message, fatal?}
   * Resolves when the stream closes; rejects on HTTP / parse errors.
   */
  async function streamMessage(message, onEvent) {
    const res = await fetch(API_BASE + "/api/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json", "Accept": "text/event-stream" },
      body: JSON.stringify({
        message: message,
        history: state.history.slice(-HISTORY_LIMIT),
        session_id: state.sessionId,
      }),
    });
    if (!res.ok || !res.body) {
      const err = new Error("HTTP " + res.status);
      err.status = res.status;
      throw err;
    }
    // Manual SSE parser — `data: {json}\n\n` per event.
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let idx;
      while ((idx = buffer.indexOf("\n\n")) !== -1) {
        const frame = buffer.slice(0, idx);
        buffer = buffer.slice(idx + 2);
        for (const line of frame.split("\n")) {
          if (!line.startsWith("data:")) continue;
          const json = line.slice(5).trim();
          if (!json) continue;
          try {
            onEvent(JSON.parse(json));
          } catch (_) {
            // Malformed frame — skip but don't tear down the whole stream.
          }
        }
      }
    }
  }

  // --- Handlers ----------------------------------------------------------

  async function onSend() {
    const text = (els.input.value || "").trim();
    if (!text || state.busy) return;
    state.busy = true;
    els.send.disabled = true;
    els.input.value = "";
    autoGrow();

    appendBubble(text, "user");
    state.history.push({ role: "user", content: text });
    const typing = showTyping();

    if (STREAMING) {
      try {
        await runStreamed(text, typing);
        return;
      } catch (e) {
        // Streaming endpoint failed before producing any output (proxy
        // buffering, 405, fatal server error before first delta). Fall
        // through to the non-streaming endpoint so the user still gets
        // an answer. Mid-stream errors don't reach here — runStreamed
        // handles them inline because partial text is already rendered.
        clearTyping();
        if (e.status === 429) {
          appendBubble("Too many messages — please wait a moment.", "bot", "error");
          finishSend();
          return;
        }
        // Otherwise: tear down any half-built streaming bubble and retry
        // on the JSON endpoint. (`streamFatal` flag is set by runStreamed
        // when no deltas arrived before the failure.)
      }
    }

    // Non-streaming fallback.
    try {
      const data = await sendMessage(text);
      clearTyping();
      appendBubble(data.answer, "bot");
      appendCitations(data.citations);
      state.history.push({ role: "assistant", content: data.answer });
      persistSession(data.session_id);
    } catch (e) {
      clearTyping();
      const detail = e.status === 429
        ? "Too many messages — please wait a moment."
        : (e.message || "Couldn't reach the assistant. Please try again.");
      appendBubble(detail, "bot", "error");
    } finally {
      finishSend();
    }
  }

  async function runStreamed(text, _typing) {
    // Streaming flow tracks four pieces of state:
    //   bubble    — the in-progress assistant DOM node (lazy on first delta)
    //   answer    — accumulated text from all deltas so far
    //   citations — set by the citations event, rendered on done
    //   doneSeen  — true if the server actually emitted a done event
    //
    // We persist `answer` to widget history regardless of whether `done`
    // arrived — otherwise a network blip after 5 deltas leaves the user's
    // next question without conversational context.
    //
    // pendingFlush batches DOM writes via requestAnimationFrame so a 60-token
    // burst doesn't cause 60 reflows on a slow phone.
    let bubble = null;
    let answer = "";
    let citations = [];
    let doneSeen = false;
    let fatal = null;
    let fatalBeforeFirstDelta = false;
    let pendingFlush = 0;

    function flushBubble() {
      if (bubble) bubble.textContent = answer;
      scrollToBottom();
      pendingFlush = 0;
    }

    try {
      await streamMessage(text, (ev) => {
        if (ev.type === "session") {
          persistSession(ev.session_id);
        } else if (ev.type === "delta") {
          if (!bubble) {
            clearTyping();
            bubble = appendBubble("", "bot");
            // Prevent the live region from re-announcing every delta — we
            // mark this bubble as "busy" until done, then expose final text.
            bubble.setAttribute("aria-busy", "true");
          }
          answer += ev.text;
          if (!pendingFlush) {
            pendingFlush = requestAnimationFrame(flushBubble);
          }
        } else if (ev.type === "citations") {
          citations = ev.citations || [];
        } else if (ev.type === "done") {
          persistSession(ev.session_id);
          doneSeen = true;
        } else if (ev.type === "error") {
          fatal = ev.message || "Stream error";
          if (!bubble) fatalBeforeFirstDelta = true;
        }
      });
    } finally {
      // Always flush the last accumulated text and persist whatever we got
      // to history — even on early disconnect / fatal error.
      if (pendingFlush) {
        cancelAnimationFrame(pendingFlush);
        flushBubble();
      }
      if (bubble) bubble.removeAttribute("aria-busy");
      if (answer.length > 0) {
        state.history.push({ role: "assistant", content: answer });
      }
    }

    // Fatal-before-any-delta: surface as an error AND let onSend retry on the
    // non-streaming endpoint (so a buffering proxy that breaks SSE still works).
    if (fatalBeforeFirstDelta) {
      const err = new Error(fatal);
      err.streamFatal = true;
      throw err;
    }

    // Normal happy path or stream that ended early after some text:
    if (doneSeen) {
      appendCitations(citations);
    } else if (fatal) {
      // Mid-stream fatal — show the error inline; partial answer is already on screen.
      const err = document.createElement("div");
      err.className = "aicw-msg bot error";
      err.textContent = fatal;
      els.body.appendChild(err);
      scrollToBottom();
    }
    finishSend();
  }

  function persistSession(sid) {
    if (sid && sid !== state.sessionId) {
      state.sessionId = sid;
      localStorage.setItem(STORAGE_KEY, sid);
    }
  }

  // Conservative: accept anything with an @ + dot (email) OR 6+ digits with
  // optional + - ( ) and spaces (phone). We're not doing real validation —
  // just catching obvious garbage like "asdfgh" before posting it to the
  // escalation channel. Empty contact is allowed (user might prefer no contact).
  const CONTACT_RE = /^([^@\s]+@[^@\s]+\.[^@\s]+|\+?[\d\s\-()]{6,})$/;

  async function onHandoff() {
    if (!state.sessionId) {
      appendBubble(
        "Send a quick message first so we have context to pass to a human.",
        "bot",
        "error",
      );
      return;
    }
    if (state.busy) return;  // never escalate mid-stream
    const contact = (els.handoffContact.value || "").trim();
    const reason = (els.handoffReason.value || "").trim();
    if (contact && !CONTACT_RE.test(contact)) {
      els.handoffContact.focus();
      els.handoffContact.style.borderColor = "#DA1E28";
      appendBubble(
        "That doesn't look like a valid email or phone — please correct it or leave it blank.",
        "bot", "error",
      );
      return;
    }
    els.handoffContact.style.borderColor = "";
    els.handoffSubmit.disabled = true;
    try {
      const res = await fetch(API_BASE + "/api/escalate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: state.sessionId,
          contact: contact || null,
          reason: reason || null,
        }),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        appendBubble(body.detail || "Could not request a human — please try again later.", "bot", "error");
        return;
      }
      els.handoffForm.classList.remove("show");
      els.handoffBtn.setAttribute("aria-expanded", "false");
      els.handoffContact.value = "";
      els.handoffReason.value = "";
      appendBubble(body.message || "We've passed your request to a human.", "bot");
    } catch (e) {
      appendBubble("Network error: " + (e.message || e), "bot", "error");
    } finally {
      els.handoffSubmit.disabled = false;
      els.input.focus();
    }
  }

  function finishSend() {
    state.busy = false;
    els.send.disabled = false;
    els.input.focus();
  }

  function togglePanel() {
    state.open = !state.open;
    els.panel.style.display = state.open ? "flex" : "none";
    els.launcher.style.display = state.open ? "none" : "flex";
    if (state.open) {
      if (state.history.length === 0) {
        appendBubble(state.config.greeting, "bot");
      }
      setTimeout(() => els.input.focus(), 80);
    }
  }

  // --- Boot --------------------------------------------------------------

  async function boot() {
    await fetchConfig();
    injectStyles(state.config.theme);
    buildLauncher();
    buildPanel();
    if (OPEN_BY_DEFAULT) togglePanel();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", boot);
  } else {
    boot();
  }
})();
