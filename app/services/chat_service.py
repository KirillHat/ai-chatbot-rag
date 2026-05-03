"""Chat orchestration: history + RAG + persistence."""

from __future__ import annotations

import logging
import uuid
from collections.abc import AsyncIterator

from app.core.claude import render_context
from app.core.rag import RAGPipeline
from app.db.database import Database
from app.models.schemas import ChatMessage, Citation

log = logging.getLogger(__name__)


class ChatService:
    def __init__(self, *, rag: RAGPipeline, db: Database):
        self.rag = rag
        self.db = db

    @staticmethod
    def new_session_id() -> str:
        return uuid.uuid4().hex

    async def reply(
        self,
        *,
        message: str,
        history: list[ChatMessage],
        session_id: str | None,
        user_agent: str | None = None,
    ) -> tuple[str, list[Citation], str, int]:
        # Don't trust client-supplied session ids: a forged uuid would let an
        # attacker append messages to someone else's chat log. We accept a
        # client id only if the server has seen it before; otherwise we mint
        # a fresh one. The widget always starts from `null` on first load
        # and persists whatever we return, so legitimate flows are unaffected.
        sid: str | None = None
        if session_id and await self.db.session_exists(session_id):
            sid = session_id
        if sid is None:
            sid = self.new_session_id()
        await self.db.upsert_session(sid, user_agent=user_agent)

        # Reduce ChatMessage → dict for the SDK; cap to last 10 turns to keep
        # the prompt cheap and predictable.
        anth_history = [{"role": m.role, "content": m.content} for m in history[-10:]]
        await self.db.log_message(session_id=sid, role="user", content=message)

        try:
            answer, retrieved, cited = await self.rag.answer(
                question=message, history=anth_history
            )
        except Exception:
            # Detailed traceback in the server log; opaque marker in the
            # client-visible chat log so we never leak Anthropic error bodies
            # (which can contain header echoes / partial keys).
            log.exception("RAG pipeline failed for session %s", sid)
            await self.db.log_message(
                session_id=sid,
                role="assistant",
                content="(error)",
            )
            raise

        citations = [
            Citation(
                document_id=c.document_id,
                document_name=c.document_name,
                snippet=_short_snippet(c.text),
                score=round(c.score, 4),
            )
            for c in cited
        ]
        await self.db.log_message(
            session_id=sid,
            role="assistant",
            content=answer,
            citations=[c.model_dump() for c in citations],
        )
        return answer, citations, sid, len({c.document_id for c in retrieved})


    async def stream_reply(
        self,
        *,
        message: str,
        history: list[ChatMessage],
        session_id: str | None,
        user_agent: str | None = None,
    ) -> AsyncIterator[dict]:
        """Stream the answer as a sequence of widget-facing events.

        Same session-trust + log policy as `reply()`. Citations and the
        final usage stats are emitted AFTER the last delta so the widget
        can render them once the answer is complete.
        """
        # 1) Session validation + persistence (same logic as reply()).
        sid: str | None = None
        if session_id and await self.db.session_exists(session_id):
            sid = session_id
        if sid is None:
            sid = self.new_session_id()
        await self.db.upsert_session(sid, user_agent=user_agent)
        anth_history = [{"role": m.role, "content": m.content} for m in history[-10:]]
        await self.db.log_message(session_id=sid, role="user", content=message)

        # Send the session_id immediately so the widget can persist it
        # even if the stream errors before completion.
        yield {"type": "session", "session_id": sid}

        # 2) Retrieve (same hybrid + optional rerank as the JSON endpoint).
        try:
            pool = self.rag.retriever.retrieve(message, top_k=self.rag.pool_size)
            if self.rag.reranker and len(pool) > 1:
                retrieved = await self.rag.reranker.rerank(message, pool, self.rag.top_k)
            else:
                retrieved = pool[: self.rag.top_k]
        except Exception:
            log.exception("Retrieval failed for session %s", sid)
            await self.db.log_message(session_id=sid, role="assistant", content="(error)")
            yield {"type": "error", "message": "Retrieval failed."}
            return

        context_block = render_context(retrieved)

        # 3) Stream the model's response.
        accumulated = []
        try:
            async for kind, payload in self.rag.claude.stream(
                user_message=message,
                history=anth_history,
                context_block=context_block,
            ):
                if kind == "delta":
                    accumulated.append(payload)
                    yield {"type": "delta", "text": payload}
                elif kind == "done":
                    # Don't forward the StreamingCompletionResult directly —
                    # it carries token counts the widget doesn't need.
                    pass
        except Exception:
            log.exception("Streaming completion failed for session %s", sid)
            await self.db.log_message(session_id=sid, role="assistant", content="(error)")
            yield {"type": "error", "message": "Generation failed."}
            return

        full_text = "".join(accumulated).strip() or "(empty reply)"

        # 4) Parse citations from the completed text.
        cited = self.rag._extract_citations(full_text, retrieved)
        citations = [
            Citation(
                document_id=c.document_id,
                document_name=c.document_name,
                snippet=_short_snippet(c.text),
                score=round(c.score, 4),
            )
            for c in cited
        ]
        # Persist the assistant turn — but never let a DB hiccup
        # (locked file, full disk, transient FS error) leave the SSE
        # stream hanging without a `done` frame. The frontend depends
        # on `done` to release `state.busy`.
        try:
            await self.db.log_message(
                session_id=sid,
                role="assistant",
                content=full_text,
                citations=[c.model_dump() for c in citations],
            )
        except Exception:
            log.exception("Failed to persist assistant turn for session %s", sid)

        yield {
            "type": "citations",
            "citations": [c.model_dump() for c in citations],
        }
        yield {
            "type": "done",
            "session_id": sid,
            "used_documents": len({c.document_id for c in retrieved}),
        }


def _short_snippet(text: str, max_len: int = 280) -> str:
    text = " ".join((text or "").split())
    return text if len(text) <= max_len else text[: max_len - 1].rstrip() + "…"
