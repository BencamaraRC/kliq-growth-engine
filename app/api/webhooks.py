"""Webhook routes — handles claim actions and email events from Brevo."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db, get_cms_db
from app.outreach.claim_handler import ClaimError, activate_store, validate_claim_token
from app.outreach.campaign_manager import send_claim_confirmation
from app.outreach.tracking import process_brevo_event

logger = logging.getLogger(__name__)

router = APIRouter()


class ClaimRequest(BaseModel):
    token: str
    password: str


class ClaimResponse(BaseModel):
    success: bool
    message: str
    redirect_url: str | None = None


@router.post("/claim", response_model=ClaimResponse)
async def claim_store(
    data: ClaimRequest,
    growth_db: AsyncSession = Depends(get_db),
    cms_db: AsyncSession = Depends(get_cms_db),
):
    """Handle store claim from coach.

    1. Validate claim token
    2. Activate store in CMS (status Draft → Active)
    3. Set coach password
    4. Send claim confirmation email
    5. Return redirect URL to CMS dashboard
    """
    try:
        prospect = await validate_claim_token(growth_db, data.token)
    except ClaimError as e:
        if "already claimed" in str(e):
            return ClaimResponse(
                success=True,
                message="Store already claimed",
                redirect_url=f"https://admin.joinkliq.io/app/{prospect.kliq_application_id}"
                if "prospect" in dir()
                else None,
            )
        raise HTTPException(status_code=404, detail=str(e))

    # Activate store
    result = await activate_store(cms_db, growth_db, prospect, data.password)

    # Send confirmation email (async, don't block)
    try:
        await send_claim_confirmation(growth_db, prospect)
    except Exception as e:
        logger.warning(f"Failed to send claim confirmation: {e}")

    return ClaimResponse(
        success=True,
        message="Store claimed successfully! Welcome to KLIQ.",
        redirect_url=result.get("store_url") or f"https://admin.joinkliq.io/app/{result['application_id']}",
    )


@router.post("/brevo")
async def brevo_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle email events from Brevo (opens, clicks, bounces, etc.)."""
    payload = await request.json()
    status = await process_brevo_event(db, payload)
    return {"status": status}
