"""Anthropic Claude client wrapper.

The wrapper is intentionally thin — it owns the system-prompt template,
retries on transient network errors and exposes a single `complete()`
method. Streaming is left out on purpose to keep the widget HTTP-simple;
the whole reply is short enough (a few hundred tokens for KB Q&A) that
streaming buys little perceived latency for the demo.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from anthropic import APIConnectionError, APIError, APITimeoutError, AsyncAnthropic
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.vectorstore import RetrievedChunk

log = logging.getLogger(__name__)

# Errors worth retrying — covers HTTP 5xx (APIError), TCP-level failures
# (APIConnectionError) and slow upstream responses (APITimeoutError). Auth /
# 4xx-style anthropic.BadRequestError NOT retried — those are bugs in our
# request, not transient.
_RETRYABLE_ANTHROPIC_ERRORS = (APIError, APIConnectionError, APITimeoutError)


SYSTEM_PROMPT_TEMPLATE = """You are {assistant_name}, a helpful customer-support assistant for {company}.

You answer questions ONLY using the provided knowledge base context. Follow these rules:

1. **Ground every answer in the context.** If the answer is not in the context,
   say so politely and offer to escalate to a human ("I don't have that
   information — would you like me to put you in touch with our team?").
2. **Cite sources inline** using bracket markers like [1], [2] that match the
   numbered context blocks below. Place the citation at the end of the
   sentence it supports.
3. **Be concise.** Default to 2–4 short sentences. Use a bulleted list only
   when the answer is genuinely a list (hours, prices, steps).
4. **Match the user's language.** If the user writes in Russian, answer in
   Russian; same for any other language present in the knowledge base.
5. **Never invent prices, dates, hours or contact details** — if the context
   is silent on a fact, don't make one up.
6. **Stay on topic.** Politely refuse off-topic requests
   (general advice, jokes, code, weather) and steer the user back.

If the context is empty, reply: "I don't have any information about that yet.
Could you rephrase, or contact us directly?"
"""


def render_context(chunks: list[RetrievedChunk]) -> str:
    """Render retrieved chunks as a numbered prompt block.

    Numbering matches the [1], [2]… citations the model is told to emit.
    """
    if not chunks:
        return "(no context found)"
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(
            f"[{i}] (source: {c.document_name})\n{c.text.strip()}"
        )
    return "\n\n".join(blocks)


@dataclass
class CompletionResult:
    text: str
    input_tokens: int
    output_tokens: int


@dataclass
class StreamingCompletionResult:
    """Aggregated stats after a streamed completion finishes."""

    text: str
    input_tokens: int
    output_tokens: int


class ClaudeClient:
    def __init__(
        self,
        api_key: str,
        model: str,
        max_tokens: int,
        assistant_name: str,
        company: str,
    ):
        self._client = AsyncAnthropic(api_key=api_key) if api_key else None
        self.model = model
        self.max_tokens = max_tokens
        self.assistant_name = assistant_name
        self.company = company

    @property
    def configured(self) -> bool:
        return self._client is not None

    def system_prompt(self) -> str:
        return SYSTEM_PROMPT_TEMPLATE.format(
            assistant_name=self.assistant_name,
            company=self.company,
        )

    async def complete(
        self,
        *,
        user_message: str,
        history: list[dict],
        context_block: str,
    ) -> CompletionResult:
        if not self._client:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set — chat is disabled. "
                "Add the key to .env and restart."
            )

        # The user's current question is appended after the retrieved context
        # block so the model always sees [context, then question] regardless
        # of conversation history.
        wrapped_user = (
            f"<knowledge_base>\n{context_block}\n</knowledge_base>\n\n"
            f"User question: {user_message}"
        )
        messages: list[dict] = [*history, {"role": "user", "content": wrapped_user}]

        async for attempt in AsyncRetrying(
            wait=wait_exponential(multiplier=0.5, min=0.5, max=4),
            stop=stop_after_attempt(3),
            retry=retry_if_exception_type(_RETRYABLE_ANTHROPIC_ERRORS),
            reraise=True,
        ):
            with attempt:
                resp = await self._client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt(),
                    messages=messages,
                )

        text_parts = [b.text for b in resp.content if getattr(b, "type", None) == "text"]
        return CompletionResult(
            text="".join(text_parts).strip() or "(empty reply)",
            input_tokens=resp.usage.input_tokens,
            output_tokens=resp.usage.output_tokens,
        )

    async def stream(
        self,
        *,
        user_message: str,
        history: list[dict],
        context_block: str,
    ):
        """Yield text deltas as they arrive from Claude.

        Yields tuples of (kind, payload):
          - ("delta", str) — incremental text chunk
          - ("done", StreamingCompletionResult) — final aggregated stats
        """
        if not self._client:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set — chat is disabled. "
                "Add the key to .env and restart."
            )

        wrapped_user = (
            f"<knowledge_base>\n{context_block}\n</knowledge_base>\n\n"
            f"User question: {user_message}"
        )
        messages: list[dict] = [*history, {"role": "user", "content": wrapped_user}]

        # Streaming intentionally does NOT retry mid-stream — once we've
        # started writing bytes to the client, retrying would duplicate
        # output. We do retry the connection setup though by attempting
        # the stream call up to 2 times before any chunks are flushed.
        last_error = None
        for attempt_n in range(2):
            try:
                async with self._client.messages.stream(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    system=self.system_prompt(),
                    messages=messages,
                ) as stream:
                    text_parts: list[str] = []
                    async for text in stream.text_stream:
                        text_parts.append(text)
                        yield ("delta", text)
                    final = await stream.get_final_message()
                    full_text = "".join(text_parts).strip() or "(empty reply)"
                    yield (
                        "done",
                        StreamingCompletionResult(
                            text=full_text,
                            input_tokens=final.usage.input_tokens,
                            output_tokens=final.usage.output_tokens,
                        ),
                    )
                    return
            except _RETRYABLE_ANTHROPIC_ERRORS as e:
                last_error = e
                log.warning("Stream attempt %d failed: %s", attempt_n + 1, e)
                continue
        # Both attempts exhausted with retryable errors — re-raise so the
        # SSE handler can convert to an error event.
        raise last_error  # type: ignore[misc]
