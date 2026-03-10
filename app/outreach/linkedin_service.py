"""LinkedIn outreach service — connection note generation + status management.

Generates personalized LinkedIn connection notes for ICF coach prospects,
manages outreach status lifecycle, and triggers ICF email sequences on
connection acceptance.
"""

import logging
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    LinkedInOutreach,
    LinkedInOutreachStatus,
    Prospect,
)

logger = logging.getLogger(__name__)

# Max LinkedIn connection note length
MAX_NOTE_LENGTH = 300

# The approved connection note template — do not change without approval
CONNECTION_NOTE_TEMPLATE = (
    "Hey {first_name}, I have sent an email over. "
    "Hope you're having a great day. "
    "I'd love to connect and share more details. "
    "Would you mind having a quick skim read and "
    "giving me a Y/N if there is any interest? "
    "Thanks Ben"
)


def _build_connection_note(prospect: Prospect) -> str:
    """Generate the personalised LinkedIn connection note (max 300 chars)."""
    first_name = prospect.first_name or prospect.name.split()[0]
    note = CONNECTION_NOTE_TEMPLATE.format(first_name=first_name)

    if len(note) > MAX_NOTE_LENGTH:
        note = note[: MAX_NOTE_LENGTH - 3] + "..."

    return note


async def generate_connection_note(session: AsyncSession, prospect_id: int) -> dict:
    """Generate a connection note for a prospect and create/update the outreach record.

    Returns dict with connection_note, linkedin_url, and status.
    """
    result = await session.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise ValueError(f"Prospect {prospect_id} not found")

    linkedin_url = prospect.linkedin_url
    if not linkedin_url:
        raise ValueError(f"Prospect {prospect_id} has no LinkedIn URL")

    note = _build_connection_note(prospect)

    # Upsert outreach record
    outreach_result = await session.execute(
        select(LinkedInOutreach).where(LinkedInOutreach.prospect_id == prospect_id)
    )
    outreach = outreach_result.scalar_one_or_none()

    if outreach:
        outreach.connection_note = note
        outreach.status = LinkedInOutreachStatus.COPIED
        outreach.copied_at = datetime.utcnow()
        outreach.linkedin_url = linkedin_url
    else:
        outreach = LinkedInOutreach(
            prospect_id=prospect_id,
            status=LinkedInOutreachStatus.COPIED,
            connection_note=note,
            linkedin_url=linkedin_url,
            copied_at=datetime.utcnow(),
        )
        session.add(outreach)

    await session.commit()

    return {
        "prospect_id": prospect_id,
        "prospect_name": prospect.name,
        "connection_note": note,
        "linkedin_url": linkedin_url,
        "status": LinkedInOutreachStatus.COPIED.value,
    }


async def update_outreach_status(session: AsyncSession, prospect_id: int, new_status: str) -> dict:
    """Update the outreach status for a prospect.

    When status is ACCEPTED, triggers the ICF email sequence.
    """
    try:
        status_enum = LinkedInOutreachStatus(new_status.upper())
    except ValueError:
        raise ValueError(f"Invalid status: {new_status}")

    outreach_result = await session.execute(
        select(LinkedInOutreach).where(LinkedInOutreach.prospect_id == prospect_id)
    )
    outreach = outreach_result.scalar_one_or_none()
    if not outreach:
        raise ValueError(f"No outreach record for prospect {prospect_id}")

    outreach.status = status_enum

    if status_enum == LinkedInOutreachStatus.SENT:
        outreach.sent_at = datetime.utcnow()
    elif status_enum == LinkedInOutreachStatus.ACCEPTED:
        outreach.accepted_at = datetime.utcnow()

    await session.commit()

    # Trigger email sequence on acceptance
    email_triggered = False
    if status_enum == LinkedInOutreachStatus.ACCEPTED:
        email_triggered = await _trigger_icf_email(session, prospect_id)

    return {
        "prospect_id": prospect_id,
        "status": status_enum.value,
        "email_triggered": email_triggered,
    }


async def _trigger_icf_email(session: AsyncSession, prospect_id: int) -> bool:
    """Trigger the ICF email sequence for an accepted LinkedIn connection."""
    from app.outreach.brevo_client import BrevoClient
    from app.outreach.campaign_manager import _send_step

    result = await session.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect or not prospect.email:
        logger.warning(
            f"Cannot trigger ICF email for prospect {prospect_id}: "
            f"{'not found' if not prospect else 'no email'}"
        )
        return False

    brevo = BrevoClient()
    success = await _send_step(session, brevo, prospect, step=1)
    if success:
        logger.info(f"ICF email triggered for prospect {prospect_id}")
    return success


async def get_linkedin_queue(
    session: AsyncSession,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[dict]:
    """Get prospects ready for LinkedIn outreach with their outreach status."""
    query = (
        select(Prospect, LinkedInOutreach)
        .outerjoin(LinkedInOutreach, LinkedInOutreach.prospect_id == Prospect.id)
        .where(Prospect.linkedin_found.is_(True))
        .order_by(Prospect.discovered_at.desc())
        .limit(limit)
    )

    if status_filter:
        try:
            status_enum = LinkedInOutreachStatus(status_filter.upper())
            query = query.where(LinkedInOutreach.status == status_enum)
        except ValueError:
            if status_filter.upper() == "QUEUED":
                # Show prospects with no outreach record (not yet contacted)
                query = query.where(LinkedInOutreach.id.is_(None))

    result = await session.execute(query)
    rows = result.all()

    queue = []
    for prospect, outreach in rows:
        niche = ""
        if prospect.niche_tags and isinstance(prospect.niche_tags, list):
            niche = prospect.niche_tags[0] if prospect.niche_tags else ""

        queue.append(
            {
                "id": prospect.id,
                "name": prospect.name,
                "email": prospect.email,
                "niche": niche,
                "linkedin_url": prospect.linkedin_url,
                "follower_count": prospect.follower_count,
                "status": outreach.status.value if outreach else "QUEUED",
                "connection_note": outreach.connection_note if outreach else None,
                "sent_at": outreach.sent_at.isoformat() if outreach and outreach.sent_at else None,
                "accepted_at": (
                    outreach.accepted_at.isoformat() if outreach and outreach.accepted_at else None
                ),
            }
        )

    return queue


async def get_linkedin_stats(session: AsyncSession) -> dict:
    """Get aggregate LinkedIn outreach statistics."""
    # Count prospects with LinkedIn URLs (the total addressable pool)
    total_result = await session.execute(
        select(func.count(Prospect.id)).where(Prospect.linkedin_found.is_(True))
    )
    total_with_linkedin = total_result.scalar() or 0

    # Count by outreach status
    status_result = await session.execute(
        select(LinkedInOutreach.status, func.count(LinkedInOutreach.id)).group_by(
            LinkedInOutreach.status
        )
    )
    status_counts = {row[0].value: row[1] for row in status_result.all()}

    # Prospects with LinkedIn but no outreach record = QUEUED
    outreach_total = sum(status_counts.values())
    queued = total_with_linkedin - outreach_total

    sent = (
        status_counts.get("SENT", 0)
        + status_counts.get("ACCEPTED", 0)
        + status_counts.get("DECLINED", 0)
        + status_counts.get("NO_RESPONSE", 0)
    )
    accepted = status_counts.get("ACCEPTED", 0)
    accept_rate = round(accepted / sent * 100, 1) if sent > 0 else 0.0

    return {
        "total_with_linkedin": total_with_linkedin,
        "queued": queued,
        "copied": status_counts.get("COPIED", 0),
        "sent": status_counts.get("SENT", 0),
        "accepted": accepted,
        "declined": status_counts.get("DECLINED", 0),
        "no_response": status_counts.get("NO_RESPONSE", 0),
        "accept_rate": accept_rate,
    }
