"""Webhook routes — handles claim actions, email events from Brevo, and Calendly bookings."""

import hashlib
import hmac
import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_cms_db, get_db
from app.outreach.calendly_processor import process_calendly_event
from app.outreach.campaign_manager import send_claim_confirmation
from app.outreach.claim_handler import ClaimError, activate_store, validate_claim_token
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
                redirect_url=f"{settings.cms_admin_url}/app/{prospect.kliq_application_id}"
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
        redirect_url=result.get("store_url")
        or f"{settings.cms_admin_url}/app/{result['application_id']}",
    )


@router.post("/brevo")
async def brevo_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle email events from Brevo (opens, clicks, bounces, etc.)."""
    payload = await request.json()
    status = await process_brevo_event(db, payload)
    return {"status": status}


@router.post("/calendly")
async def calendly_webhook(request: Request, db: AsyncSession = Depends(get_db)):
    """Handle Calendly webhook events (invitee.created, invitee.canceled).

    Validates the webhook signature if a secret is configured, then
    creates/updates booking records and links them to prospects.
    """
    body = await request.body()

    # Validate webhook signature if secret is configured
    if settings.calendly_webhook_secret:
        signature = request.headers.get("Calendly-Webhook-Signature", "")
        if not _verify_calendly_signature(body, signature, settings.calendly_webhook_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")

    payload = await request.json()
    status = await process_calendly_event(db, payload)
    return {"status": status}


def _verify_calendly_signature(body: bytes, signature_header: str, secret: str) -> bool:
    """Verify Calendly webhook signature.

    Calendly sends a signature header in the format:
    t=<timestamp>,v1=<signature>
    """
    if not signature_header:
        return False

    try:
        parts = {}
        for item in signature_header.split(","):
            key, value = item.split("=", 1)
            parts[key.strip()] = value.strip()

        timestamp = parts.get("t", "")
        expected_sig = parts.get("v1", "")

        if not timestamp or not expected_sig:
            return False

        # Calendly signs: timestamp.body
        signed_payload = f"{timestamp}.{body.decode('utf-8')}"
        computed = hmac.new(
            secret.encode("utf-8"),
            signed_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(computed, expected_sig)
    except (ValueError, KeyError):
        return False
