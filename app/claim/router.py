"""Claim flow routes — serves the claim page, handles form submission, and onboarding."""

import logging

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.claim.queries import (
    get_auto_login_token,
    get_content_counts,
    get_onboarding_dict,
    get_prospect_by_token,
)
from app.claim.renderer import (
    render_already_claimed_page,
    render_claim_page,
    render_error_page,
    render_welcome_page,
)
from app.db.session import get_cms_db, get_db
from app.outreach.claim_handler import ClaimError, activate_store, validate_claim_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/claim", response_class=HTMLResponse)
async def claim_page(
    token: str = Query(...),
    session: AsyncSession = Depends(get_db),
):
    """Serve the claim page with the password form."""
    prospect = await get_prospect_by_token(session, token)

    if not prospect:
        return HTMLResponse(
            content=render_error_page(
                title="Invalid Link",
                message="This claim link is invalid or has expired. Please check your email for the correct link.",
                cta_url="https://joinkliq.io",
                cta_text="Visit KLIQ",
            ),
            status_code=404,
        )

    if prospect["status"] == "CLAIMED":
        return HTMLResponse(content=render_already_claimed_page(prospect))

    content_counts = await get_content_counts(session, prospect["id"])
    return HTMLResponse(content=render_claim_page(prospect, content_counts))


@router.post("/claim", response_class=HTMLResponse)
async def claim_submit(
    request: Request,
    growth_db: AsyncSession = Depends(get_db),
    cms_db: AsyncSession = Depends(get_cms_db),
):
    """Handle the claim form submission."""
    form = await request.form()
    token = form.get("token", "")
    password = form.get("password", "")
    password_confirm = form.get("password_confirm", "")

    # Server-side validation
    errors = []
    if not token:
        errors.append("Missing claim token.")
    if len(password) < 8:
        errors.append("Password must be at least 8 characters.")
    if password != password_confirm:
        errors.append("Passwords do not match.")

    if errors:
        prospect = await get_prospect_by_token(growth_db, token)
        if not prospect:
            return HTMLResponse(
                content=render_error_page(
                    title="Invalid Link",
                    message="This claim link is invalid or has expired.",
                    cta_url="https://joinkliq.io",
                    cta_text="Visit KLIQ",
                ),
                status_code=404,
            )
        content_counts = await get_content_counts(growth_db, prospect["id"])
        return HTMLResponse(content=render_claim_page(prospect, content_counts, errors=errors))

    # Activate the store using existing claim handler
    try:
        prospect_obj = await validate_claim_token(growth_db, token)
        await activate_store(cms_db, growth_db, prospect_obj, password)
    except ClaimError as e:
        error_msg = str(e)
        if "already claimed" in error_msg.lower():
            prospect = await get_prospect_by_token(growth_db, token)
            if prospect:
                return HTMLResponse(content=render_already_claimed_page(prospect))
        return HTMLResponse(
            content=render_error_page(
                title="Claim Failed",
                message=error_msg,
                cta_url="https://joinkliq.io",
                cta_text="Visit KLIQ",
            ),
            status_code=400,
        )

    # Send claim confirmation email (non-blocking)
    try:
        from app.outreach.campaign_manager import send_claim_confirmation

        await send_claim_confirmation(growth_db, prospect_obj)
    except Exception:
        logger.exception("Failed to send claim confirmation email")

    # Redirect to welcome page
    return RedirectResponse(url=f"/welcome?token={token}", status_code=303)


@router.get("/welcome", response_class=HTMLResponse)
async def welcome_page(
    token: str = Query(...),
    session: AsyncSession = Depends(get_db),
    cms_db: AsyncSession = Depends(get_cms_db),
):
    """Serve the onboarding/welcome page after claiming."""
    prospect = await get_prospect_by_token(session, token)

    if not prospect:
        return HTMLResponse(
            content=render_error_page(
                title="Page Not Found",
                message="We couldn't find your store. Please check your email for the correct link.",
                cta_url="https://joinkliq.io",
                cta_text="Visit KLIQ",
            ),
            status_code=404,
        )

    # If not yet claimed, redirect to claim page
    if prospect["status"] != "CLAIMED":
        return RedirectResponse(url=f"/claim?token={token}")

    # Fetch auto-login token from CMS for seamless dashboard access
    auto_login_token = await get_auto_login_token(cms_db, prospect)

    content_counts = await get_content_counts(session, prospect["id"])
    onboarding = await get_onboarding_dict(session, prospect["id"])
    return HTMLResponse(
        content=render_welcome_page(
            prospect, content_counts, auto_login_token=auto_login_token, onboarding=onboarding
        )
    )
