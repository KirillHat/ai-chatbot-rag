"""Public hand-off endpoint — `POST /api/escalate`.

Same rate limiter as `/api/chat` so a malicious widget can't spam the
escalation channel with thousands of bogus events.
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.api.deps import rate_limit_escalate
from app.models.schemas import EscalateRequest, EscalateResponse
from app.services.escalation_service import EscalationService

router = APIRouter(prefix="/api", tags=["escalate"], dependencies=[Depends(rate_limit_escalate)])
log = logging.getLogger(__name__)


def get_escalation(request: Request) -> EscalationService:
    return request.app.state.escalation


@router.post(
    "/escalate",
    response_model=EscalateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def escalate(
    payload: EscalateRequest,
    service: Annotated[EscalationService, Depends(get_escalation)],
) -> EscalateResponse:
    try:
        result = await service.escalate(
            session_id=payload.session_id,
            contact=payload.contact,
            reason=payload.reason,
        )
    except Exception as e:
        log.exception("Escalation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not record the escalation request — please try again.",
        ) from e

    if result.notified:
        msg = f"We've passed your request to a human (ref #{result.id}). They'll be in touch shortly."
    else:
        msg = (
            f"Your request was logged (ref #{result.id}), but no notification "
            "channel is configured on this server yet."
        )
    return EscalateResponse(
        id=result.id,
        status="received",
        notified=result.notified,
        message=msg,
    )
