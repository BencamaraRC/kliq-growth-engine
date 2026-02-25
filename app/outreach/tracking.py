"""Email event tracking — processes webhook events from Brevo.

Handles: opened, click, hard_bounce, soft_bounce, unsubscribed, delivered.
Updates CampaignEvent records in the Growth DB.
"""

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import CampaignEvent, EmailStatus, Prospect, ProspectStatus

logger = logging.getLogger(__name__)

# Map Brevo event names to our EmailStatus enum
EVENT_MAP = {
    "delivered": EmailStatus.SENT,
    "opened": EmailStatus.OPENED,
    "click": EmailStatus.CLICKED,
    "hard_bounce": EmailStatus.BOUNCED,
    "soft_bounce": EmailStatus.BOUNCED,
    "unsubscribed": EmailStatus.UNSUBSCRIBED,
}


async def process_brevo_event(session: AsyncSession, payload: dict) -> str:
    """Process a Brevo webhook event.

    Args:
        session: Growth DB session.
        payload: Raw webhook payload from Brevo.

    Returns:
        Processing status string.
    """
    event_type = payload.get("event")
    message_id = payload.get("message-id")

    if not message_id or not event_type:
        return "ignored"

    new_status = EVENT_MAP.get(event_type)
    if not new_status:
        logger.debug(f"Unhandled Brevo event type: {event_type}")
        return "ignored"

    # Find the campaign event by Brevo message ID
    result = await session.execute(
        select(CampaignEvent).where(CampaignEvent.brevo_message_id == message_id)
    )
    event = result.scalar_one_or_none()

    if not event:
        logger.debug(f"No campaign event found for message_id={message_id}")
        return "not_found"

    now = datetime.utcnow()

    # Update event status and timestamps
    event.email_status = new_status

    if event_type == "opened" and not event.opened_at:
        event.opened_at = now
    elif event_type == "click" and not event.clicked_at:
        event.clicked_at = now

    # If bounced or unsubscribed, mark the prospect to prevent further emails
    if new_status in (EmailStatus.BOUNCED, EmailStatus.UNSUBSCRIBED):
        prospect = await session.get(Prospect, event.prospect_id)
        if prospect:
            prospect.status = ProspectStatus.REJECTED
            logger.info(f"Prospect {prospect.id} marked as rejected ({event_type})")

    await session.commit()

    logger.info(f"Processed Brevo event: {event_type} for message_id={message_id}")
    return "processed"
