"""Campaign manager — orchestrates the 7-step email outreach lifecycle.

Manages the timing and sequencing of outreach emails:
  Step 1: Initial outreach (platform-specific) — immediately after store creation
  Step 2: Gentle Nudge — Day 3
  Step 3: Value Add — Day 6
  Step 4: Social Proof — Day 10
  Step 5: Preview Activity — Day 14
  Step 6: New Angle — Day 21
  Step 7: Breakup — Day 28
  Step 8: Claimed confirmation — immediately on claim

Sequencing rules:
  - If the prospect replies at any point, the automated sequence stops
  - If the prospect claims their store, all follow-ups are cancelled
  - All emails sent from growth@joinkliq.io via Brevo
"""

import json as _json
import logging
from datetime import datetime, timedelta

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    Campaign,
    CampaignEvent,
    CampaignStatus,
    EmailStatus,
    OnboardingProgress,
    Prospect,
    ProspectStatus,
)
from app.outreach.brevo_client import BrevoClient
from app.outreach.email_builder import ONBOARDING_STEPS, STEPS, build_outreach_email

logger = logging.getLogger(__name__)

# Follow-up steps with (step_number, days_since_step_1)
# Step 1 is sent at Day 0; subsequent steps fire at absolute day offsets from Step 1
FOLLOW_UP_SCHEDULE = [
    # (step, days_after_initial)
    (2, 3),  # Gentle Nudge
    (3, 6),  # Value Add
    (4, 10),  # Social Proof
    (5, 14),  # Preview Activity
    (6, 21),  # New Angle
    (7, 28),  # Breakup
]


DAILY_SEND_LIMIT = settings.daily_email_send_limit


async def _get_today_send_count(session: AsyncSession) -> int:
    """Count emails sent today to enforce the daily limit."""
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(CampaignEvent).where(
            and_(
                CampaignEvent.email_status == EmailStatus.SENT,
                CampaignEvent.sent_at >= today_start,
            )
        )
    )
    return len(result.scalars().all())


async def process_outreach(session: AsyncSession) -> dict:
    """Process all pending outreach actions.

    Called periodically (every 30 min) by the Celery beat scheduler.
    Finds prospects that need emails and sends them.
    Respects DAILY_SEND_LIMIT to control volume.

    Returns:
        Summary of actions taken.
    """
    results = {
        "initial_sends": 0,
        "followups_sent": 0,
        "errors": 0,
        "skipped_limit": 0,
    }

    sent_today = await _get_today_send_count(session)
    remaining = DAILY_SEND_LIMIT - sent_today

    if remaining <= 0:
        logger.info(f"Daily send limit reached ({sent_today}/{DAILY_SEND_LIMIT}), skipping")
        results["skipped_limit"] = 1
        return results

    brevo = BrevoClient()

    # 1. Find prospects with stores but no email sent yet (Step 1)
    new_prospects = await _find_unsent_prospects(session)
    for prospect in new_prospects:
        if remaining <= 0:
            results["skipped_limit"] += 1
            continue
        success = await _send_step(session, brevo, prospect, step=1)
        if success:
            results["initial_sends"] += 1
            remaining -= 1
        else:
            results["errors"] += 1

    # 2. Process follow-up steps 2-7 based on days since initial email
    for step_num, days_after_initial in FOLLOW_UP_SCHEDULE:
        if remaining <= 0:
            break
        due_prospects = await _find_due_for_followup(session, step_num, days_after_initial)
        for prospect in due_prospects:
            if remaining <= 0:
                results["skipped_limit"] += 1
                continue
            success = await _send_step(session, brevo, prospect, step=step_num)
            if success:
                results["followups_sent"] += 1
                remaining -= 1
            else:
                results["errors"] += 1

    logger.info(
        f"Outreach processing complete: {results} "
        f"(sent today: {DAILY_SEND_LIMIT - remaining}/{DAILY_SEND_LIMIT})"
    )
    return results


async def send_claim_confirmation(session: AsyncSession, prospect: Prospect):
    """Send the claim confirmation email (Step 8).

    Called when a coach claims their store.
    """
    brevo = BrevoClient()
    await _send_step(session, brevo, prospect, step=8)
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
    if existing.scalars().first():
        logger.debug(f"Step {step} already sent for prospect {prospect.id}")
        return False

    # Build the email
    colors = prospect.brand_colors or []
    primary_color = f"#{colors[0]}" if colors else "#1E81FF"

    preview_url = f"{settings.app_base_url}/preview?token={prospect.claim_token}"

    # Load generated content counts, tagline, and niche
    from app.db.models import GeneratedContent

    gen_result = await session.execute(
        select(GeneratedContent).where(GeneratedContent.prospect_id == prospect.id)
    )
    gen_records = gen_result.scalars().all()
    blog_count = sum(1 for g in gen_records if g.content_type == "blog")
    product_count = sum(1 for g in gen_records if g.content_type == "product")
    tagline = ""
    niche = ""
    for g in gen_records:
        if g.content_type == "bio":
            try:
                bio_data = _json.loads(g.body)
                tagline = bio_data.get("tagline", "")
                niche = bio_data.get("niche", "")
            except (ValueError, TypeError):
                pass
            break

    # Fallback niche from prospect niche_tags
    if not niche and prospect.niche_tags:
        tags = prospect.niche_tags
        if isinstance(tags, str):
            try:
                tags = _json.loads(tags)
            except (ValueError, TypeError):
                tags = []
        if tags:
            niche = tags[0]

    # Get preview view count (for step 5)
    view_count = await _get_preview_view_count(session, prospect.id)

    # Pre-send check: verify the preview page is reachable (steps 1-7 link to it)
    if step <= 7 and prospect.claim_token:
        import urllib.request

        try:
            check_req = urllib.request.Request(preview_url, method="GET")
            with urllib.request.urlopen(check_req, timeout=5) as resp:
                if resp.status != 200:
                    logger.error(
                        f"Preview URL returned {resp.status} for prospect {prospect.id}, "
                        f"skipping step {step}"
                    )
                    return False
        except Exception as e:
            logger.error(
                f"Preview URL unreachable for prospect {prospect.id}: {e}, skipping step {step}"
            )
            return False

    email = build_outreach_email(
        step=step,
        email=prospect.email,
        first_name=prospect.first_name or prospect.name.split()[0],
        store_name=prospect.name,
        platform=prospect.primary_platform.value if prospect.primary_platform else "YOUTUBE",
        claim_token=prospect.claim_token or "",
        primary_color=primary_color,
        tagline=tagline,
        blog_count=blog_count,
        product_count=product_count,
        store_url=preview_url,
        application_id=prospect.kliq_application_id,
        profile_image_url=prospect.profile_image_url or "",
        niche=niche,
        view_count=view_count,
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
        from app.events.bigquery import log_event

        log_event(
            "email_sent",
            prospect_id=prospect.id,
            campaign_id=campaign.id,
            email_step=step,
        )
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


async def _find_due_for_followup(
    session: AsyncSession,
    step: int,
    days_after_initial: int,
) -> list[Prospect]:
    """Find prospects due for a specific follow-up step.

    Uses absolute day offset from the initial email (Step 1) to determine timing.
    Returns prospects where:
    - Step 1 was sent at least `days_after_initial` days ago
    - Store is still unclaimed (not CLAIMED or REJECTED)
    - This step hasn't been sent yet
    - No bounce/unsubscribe on any previous step
    """
    cutoff = datetime.utcnow() - timedelta(days=days_after_initial)

    # Find Step 1 events that are old enough
    result = await session.execute(
        select(CampaignEvent, Prospect)
        .join(Prospect, CampaignEvent.prospect_id == Prospect.id)
        .where(
            and_(
                CampaignEvent.step == 1,
                CampaignEvent.email_status.in_(
                    [EmailStatus.SENT, EmailStatus.OPENED, EmailStatus.CLICKED]
                ),
                CampaignEvent.sent_at <= cutoff,
                Prospect.status.notin_([ProspectStatus.CLAIMED, ProspectStatus.REJECTED]),
            )
        )
    )
    rows = result.all()

    # Filter out those that already received this step or have bounced/unsubscribed
    due = []
    for event, prospect in rows:
        # Check if this step already sent
        existing = await session.execute(
            select(CampaignEvent).where(
                and_(
                    CampaignEvent.prospect_id == prospect.id,
                    CampaignEvent.step == step,
                )
            )
        )
        if existing.scalars().first():
            continue

        # Check for bounce/unsubscribe on any step
        bounced = await session.execute(
            select(CampaignEvent).where(
                and_(
                    CampaignEvent.prospect_id == prospect.id,
                    CampaignEvent.email_status.in_([EmailStatus.BOUNCED, EmailStatus.UNSUBSCRIBED]),
                )
            )
        )
        if bounced.scalars().first():
            continue

        due.append(prospect)

    return due


async def _get_preview_view_count(session: AsyncSession, prospect_id: int) -> int:
    """Get the number of times the preview page has been viewed.

    Falls back to 0 if no tracking data exists.
    """
    # Check if we have click events (proxy for views)
    result = await session.execute(
        select(CampaignEvent).where(
            and_(
                CampaignEvent.prospect_id == prospect_id,
                CampaignEvent.email_status == EmailStatus.CLICKED,
            )
        )
    )
    clicks = len(result.scalars().all())
    return clicks


async def process_onboarding_emails(session: AsyncSession) -> dict:
    """Send follow-up onboarding emails (steps 9-10) to claimed coaches.

    For each step:
    - Find claimed prospects past the delay cutoff (from claimed_at)
    - Skip if the relevant onboarding step is already complete
    - Send via existing _send_step() which handles duplicate checking

    Called every 6 hours by Celery Beat.
    """
    results = {"sent": 0, "skipped": 0, "errors": 0}
    brevo = BrevoClient()

    for step_num in ONBOARDING_STEPS:
        step_config = STEPS[step_num]
        delay_days = step_config["delay_days"]
        skip_field = step_config.get("skip_if")
        cutoff = datetime.utcnow() - timedelta(days=delay_days)

        # Find claimed prospects past the delay
        query = (
            select(Prospect, OnboardingProgress)
            .outerjoin(OnboardingProgress, OnboardingProgress.prospect_id == Prospect.id)
            .where(
                Prospect.status == ProspectStatus.CLAIMED,
                Prospect.claimed_at <= cutoff,
                Prospect.email.is_not(None),
            )
        )
        result = await session.execute(query)
        rows = result.all()

        for prospect, onboarding in rows:
            # Skip if onboarding step already complete
            if onboarding and skip_field and getattr(onboarding, skip_field, False):
                results["skipped"] += 1
                continue

            success = await _send_step(session, brevo, prospect, step=step_num)
            if success:
                results["sent"] += 1
            else:
                # _send_step returns False for duplicates too, not just errors
                results["skipped"] += 1

    logger.info(f"Onboarding emails processed: {results}")
    return results


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
