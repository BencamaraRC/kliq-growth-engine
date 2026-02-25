"""Campaign manager — orchestrates the 4-step email outreach lifecycle.

Manages the timing and sequencing of outreach emails:
  Step 1: "Your store is ready" — immediately after store creation
  Step 2: Reminder 1 — +3 days if unclaimed
  Step 3: Reminder 2 — +7 days if unclaimed
  Step 4: Claimed confirmation — immediately on claim

Queries the database for prospects that need emails and schedules sends.
"""

import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    Campaign,
    CampaignEvent,
    CampaignStatus,
    EmailStatus,
    Prospect,
    ProspectStatus,
)
from app.outreach.brevo_client import BrevoClient
from app.outreach.email_builder import STEPS, build_outreach_email

logger = logging.getLogger(__name__)


async def process_outreach(session: AsyncSession) -> dict:
    """Process all pending outreach actions.

    Called periodically (every 30 min) by the Celery beat scheduler.
    Finds prospects that need emails and sends them.

    Returns:
        Summary of actions taken.
    """
    results = {
        "initial_sends": 0,
        "reminders_sent": 0,
        "errors": 0,
    }

    brevo = BrevoClient()

    # 1. Find prospects with stores but no email sent yet (Step 1)
    new_prospects = await _find_unsent_prospects(session)
    for prospect in new_prospects:
        success = await _send_step(session, brevo, prospect, step=1)
        if success:
            results["initial_sends"] += 1
        else:
            results["errors"] += 1

    # 2. Find prospects due for Reminder 1 (Step 2, +3 days)
    due_step_2 = await _find_due_for_step(session, step=2, days_since_last=3)
    for prospect, last_event in due_step_2:
        success = await _send_step(session, brevo, prospect, step=2)
        if success:
            results["reminders_sent"] += 1
        else:
            results["errors"] += 1

    # 3. Find prospects due for Reminder 2 (Step 3, +7 days from first email)
    due_step_3 = await _find_due_for_step(session, step=3, days_since_last=4)
    for prospect, last_event in due_step_3:
        success = await _send_step(session, brevo, prospect, step=3)
        if success:
            results["reminders_sent"] += 1
        else:
            results["errors"] += 1

    logger.info(f"Outreach processing complete: {results}")
    return results


async def send_claim_confirmation(session: AsyncSession, prospect: Prospect):
    """Send the claim confirmation email (Step 4).

    Called when a coach claims their store.
    """
    brevo = BrevoClient()
    await _send_step(session, brevo, prospect, step=4)
    logger.info(f"Claim confirmation sent to {prospect.email}")


async def _send_step(
    session: AsyncSession,
    brevo: BrevoClient,
    prospect: Prospect,
    step: int,
) -> bool:
    """Send a specific campaign step email to a prospect.

    Creates a CampaignEvent record and sends the email via Brevo.
    """
    if not prospect.email:
        logger.warning(f"No email for prospect {prospect.id}, skipping step {step}")
        return False

    # Get or create active campaign
    campaign = await _get_active_campaign(session)

    # Check if already sent this step
    existing = await session.execute(
        select(CampaignEvent).where(
            and_(
                CampaignEvent.prospect_id == prospect.id,
                CampaignEvent.campaign_id == campaign.id,
                CampaignEvent.step == step,
            )
        )
    )
    if existing.scalar_one_or_none():
        logger.debug(f"Step {step} already sent for prospect {prospect.id}")
        return False

    # Build the email
    colors = prospect.brand_colors or []
    primary_color = f"#{colors[0]}" if colors else "#1E81FF"

    email = build_outreach_email(
        step=step,
        email=prospect.email,
        first_name=prospect.first_name or prospect.name.split()[0],
        store_name=prospect.name,
        platform=prospect.primary_platform.value if prospect.primary_platform else "YouTube",
        claim_token=prospect.claim_token or "",
        primary_color=primary_color,
        store_url=prospect.kliq_store_url or "",
        application_id=prospect.kliq_application_id,
    )

    # Send via Brevo
    result = brevo.send_email(
        to_email=email.to_email,
        to_name=email.to_name,
        subject=email.subject,
        html_content=email.html_content,
        tags=email.tags,
    )

    # Record the event
    event = CampaignEvent(
        campaign_id=campaign.id,
        prospect_id=prospect.id,
        step=step,
        email_status=EmailStatus.SENT if result.success else EmailStatus.BOUNCED,
        sent_at=datetime.utcnow() if result.success else None,
        brevo_message_id=result.message_id,
    )
    session.add(event)

    # Update prospect status if this is the first email
    if step == 1 and result.success:
        prospect.status = ProspectStatus.EMAIL_SENT

    await session.commit()

    if result.success:
        logger.info(f"Sent step {step} to {prospect.email} (message_id={result.message_id})")
    else:
        logger.error(f"Failed step {step} to {prospect.email}: {result.error}")

    return result.success


async def _find_unsent_prospects(session: AsyncSession) -> list[Prospect]:
    """Find prospects with stores created but no email sent yet."""
    result = await session.execute(
        select(Prospect).where(
            Prospect.status == ProspectStatus.STORE_CREATED,
            Prospect.email.is_not(None),
            Prospect.claim_token.is_not(None),
        )
    )
    return list(result.scalars().all())


async def _find_due_for_step(
    session: AsyncSession,
    step: int,
    days_since_last: int,
) -> list[tuple[Prospect, CampaignEvent]]:
    """Find prospects due for a specific follow-up step.

    Returns prospects where:
    - Previous step was sent
    - Enough time has elapsed since the previous step
    - Store is still unclaimed
    - This step hasn't been sent yet
    """
    previous_step = step - 1
    cutoff = datetime.utcnow() - timedelta(days=days_since_last)

    # Find last events for the previous step that are old enough
    result = await session.execute(
        select(CampaignEvent, Prospect)
        .join(Prospect, CampaignEvent.prospect_id == Prospect.id)
        .where(
            and_(
                CampaignEvent.step == previous_step,
                CampaignEvent.email_status.in_([EmailStatus.SENT, EmailStatus.OPENED, EmailStatus.CLICKED]),
                CampaignEvent.sent_at <= cutoff,
                Prospect.status != ProspectStatus.CLAIMED,
                Prospect.status != ProspectStatus.REJECTED,
            )
        )
    )
    rows = result.all()

    # Filter out those that already received this step
    due = []
    for event, prospect in rows:
        existing = await session.execute(
            select(CampaignEvent).where(
                and_(
                    CampaignEvent.prospect_id == prospect.id,
                    CampaignEvent.step == step,
                )
            )
        )
        if not existing.scalar_one_or_none():
            due.append((prospect, event))

    return due


async def _get_active_campaign(session: AsyncSession) -> Campaign:
    """Get or create the active Growth Engine campaign."""
    result = await session.execute(
        select(Campaign).where(Campaign.status == CampaignStatus.ACTIVE).limit(1)
    )
    campaign = result.scalar_one_or_none()

    if not campaign:
        campaign = Campaign(
            name="Growth Engine Auto-Outreach",
            status=CampaignStatus.ACTIVE,
        )
        session.add(campaign)
        await session.flush()

    return campaign
