"""Processes Calendly webhook events — creates bookings and updates prospect status."""

import logging
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def process_calendly_event(db: AsyncSession, payload: dict) -> str:
    """Process a Calendly webhook payload.

    Handles invitee.created and invitee.canceled events:
    - Matches invitee email to a prospect
    - Creates/updates CalendlyBooking record
    - Updates LinkedIn outreach status to BOOKED_DEMO if applicable

    Returns a status string: 'created', 'canceled', 'no_match', or 'ignored'.
    """
    event_type = payload.get("event")

    if event_type == "invitee.created":
        return await _handle_booking_created(db, payload)
    elif event_type == "invitee.canceled":
        return await _handle_booking_canceled(db, payload)
    else:
        logger.info(f"Ignoring Calendly event type: {event_type}")
        return "ignored"


async def _handle_booking_created(db: AsyncSession, payload: dict) -> str:
    """Handle a new Calendly booking (invitee.created)."""
    invitee_payload = payload.get("payload", {})
    invitee_email = invitee_payload.get("email", "").lower().strip()
    calendly_event_id = invitee_payload.get("uri", "") or invitee_payload.get("event", "")
    event_type_name = invitee_payload.get("event_type", {}).get("name", "")
    scheduled_at_str = invitee_payload.get("scheduled_event", {}).get("start_time")
    booked_at_str = invitee_payload.get("created_at")

    if not invitee_email:
        logger.warning("Calendly event missing invitee email")
        return "ignored"

    # Parse timestamps
    scheduled_at = _parse_iso(scheduled_at_str)
    booked_at = _parse_iso(booked_at_str) or datetime.utcnow()

    # Use the event URI as the unique ID (or fall back to a composite)
    event_id = calendly_event_id or f"{invitee_email}:{scheduled_at_str}"

    # Match to prospect by email
    prospect_row = await db.execute(
        text("SELECT id FROM prospects WHERE LOWER(email) = :email"),
        {"email": invitee_email},
    )
    prospect = prospect_row.fetchone()

    if not prospect:
        logger.info(f"No prospect found for Calendly invitee: {invitee_email}")
        return "no_match"

    prospect_id = prospect[0]

    # Insert booking (upsert on calendly_event_id)
    await db.execute(
        text("""
            INSERT INTO calendly_bookings
                (prospect_id, calendly_event_id, invitee_email, event_type,
                 scheduled_at, booked_at, status)
            VALUES
                (:prospect_id, :event_id, :email, :event_type,
                 :scheduled_at, :booked_at, 'SCHEDULED')
            ON CONFLICT (calendly_event_id) DO UPDATE SET
                scheduled_at = EXCLUDED.scheduled_at,
                status = 'SCHEDULED',
                canceled_at = NULL,
                updated_at = now()
        """),
        {
            "prospect_id": prospect_id,
            "event_id": event_id,
            "email": invitee_email,
            "event_type": event_type_name,
            "scheduled_at": scheduled_at,
            "booked_at": booked_at,
        },
    )

    # Update LinkedIn outreach status to BOOKED_DEMO if they have one
    await db.execute(
        text("""
            UPDATE linkedin_outreach
            SET status = 'BOOKED_DEMO', updated_at = now()
            WHERE prospect_id = :pid
              AND status IN ('SENT', 'ACCEPTED', 'NO_RESPONSE')
        """),
        {"pid": prospect_id},
    )

    await db.commit()
    logger.info(f"Calendly booking created for prospect {prospect_id} ({invitee_email})")
    return "created"


async def _handle_booking_canceled(db: AsyncSession, payload: dict) -> str:
    """Handle a Calendly cancellation (invitee.canceled)."""
    invitee_payload = payload.get("payload", {})
    calendly_event_id = invitee_payload.get("uri", "") or invitee_payload.get("event", "")
    canceled_at_str = invitee_payload.get("canceled_at") or invitee_payload.get("updated_at")

    if not calendly_event_id:
        logger.warning("Calendly cancel event missing event ID")
        return "ignored"

    canceled_at = _parse_iso(canceled_at_str) or datetime.utcnow()

    result = await db.execute(
        text("""
            UPDATE calendly_bookings
            SET status = 'CANCELED', canceled_at = :canceled_at, updated_at = now()
            WHERE calendly_event_id = :event_id
            RETURNING prospect_id
        """),
        {"event_id": calendly_event_id, "canceled_at": canceled_at},
    )
    row = result.fetchone()

    if not row:
        logger.info(f"No booking found for Calendly event: {calendly_event_id}")
        return "no_match"

    await db.commit()
    logger.info(f"Calendly booking canceled for prospect {row[0]}")
    return "canceled"


def _parse_iso(s: str | None) -> datetime | None:
    """Parse an ISO 8601 timestamp string, returning None on failure."""
    if not s:
        return None
    try:
        # Handle Calendly's format: 2026-03-11T14:00:00.000000Z
        s = s.replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return None
