"""Widget configuration endpoint.

Returns the small JSON blob the embeddable widget reads on load — the
bot's display name, greeting and theme. Lets the same JS bundle serve
multiple sites without rebuilding.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.deps import SettingsDep

router = APIRouter(prefix="/api", tags=["widget"])


@router.get("/widget/config")
async def widget_config(settings: SettingsDep) -> dict:
    return {
        "tenant": settings.assistant_tenant,
        "name": settings.assistant_name,
        "greeting": (
            f"Hi! I'm {settings.assistant_name}. "
            "Ask me anything about our services."
        ),
        "placeholder": "Type your question…",
        "theme": {
            "primary": "#0F62FE",
            "background": "#FFFFFF",
            "userBubble": "#0F62FE",
            "botBubble": "#F2F4F8",
        },
        "poweredBy": "Claude · RAG",
    }
