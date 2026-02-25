"""Webhook routes — handles claim actions and email events from Brevo."""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CampaignEvent, EmailStatus, Prospect, ProspectStatus
from app.db.session import get_db

router = APIRouter()


class ClaimRequest(BaseModel):
    token: str
    password: str


class ClaimResponse(BaseModel):
    success: bool
    message: str
    redirect_url: str | None = None


@router.post("/claim", response_model=ClaimResponse)
async def claim_store(data: ClaimRequest, db: AsyncSession = Depends(get_db)):
    """Handle store claim from coach.

    1. Validate claim token
    2. Update prospect status to CLAIMED
    3. Activate store in CMS (status 1 → 2)
    4. Set coach password
    5. Return redirect URL to CMS dashboard
    """
    result = await db.execute(
        select(Prospect).where(Prospect.claim_token == data.token)
    )
    prospect = result.scalar_one_or_none()

    if not prospect:
        raise HTTPException(status_code=404, detail="Invalid claim token")

    if prospect.status == ProspectStatus.CLAIMED:
        return ClaimResponse(
            success=True,
            message="Store already claimed",
            redirect_url=prospect.kliq_store_url,
        )

    # TODO: Activate store in CMS MySQL (Phase 3)
    # TODO: Set coach password in CMS (Phase 3)

    prospect.status = ProspectStatus.CLAIMED
    from datetime import datetime

    prospect.claimed_at = datetime.utcnow()
    await db.commit()

    return ClaimResponse(
        success=True,
        message="Store claimed successfully!",
        redirect_url=prospect.kliq_store_url,
    )


@router.post("/brevo")
async def brevo_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle email events from Brevo (opens, clicks, bounces, etc.)."""
    payload = await request.json()
    event_type = payload.get("event")
    message_id = payload.get("message-id")

    if not message_id:
        return {"status": "ignored"}

    result = await db.execute(
        select(CampaignEvent).where(CampaignEvent.brevo_message_id == message_id)
    )
    event = result.scalar_one_or_none()
    if not event:
        return {"status": "not_found"}

    from datetime import datetime

    now = datetime.utcnow()

    if event_type == "opened":
        event.email_status = EmailStatus.OPENED
        event.opened_at = now
    elif event_type == "click":
        event.email_status = EmailStatus.CLICKED
        event.clicked_at = now
    elif event_type in ("hard_bounce", "soft_bounce"):
        event.email_status = EmailStatus.BOUNCED
    elif event_type == "unsubscribed":
        event.email_status = EmailStatus.UNSUBSCRIBED

    await db.commit()
    return {"status": "processed"}
