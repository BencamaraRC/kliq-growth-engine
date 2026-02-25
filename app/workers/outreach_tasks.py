"""Celery tasks for email outreach.

Handles:
- Sending individual outreach emails (triggered by pipeline or manually)
- Processing the outreach queue (periodic, finds due reminders)
"""

import asyncio
import logging

from app.db.session import async_session
from app.outreach.campaign_manager import process_outreach
from app.outreach.brevo_client import BrevoClient
from app.outreach.email_builder import build_outreach_email
from app.db.models import CampaignEvent, Campaign, CampaignStatus, EmailStatus, Prospect
from app.workers.celery_app import celery_app
from sqlalchemy import select

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Bridge sync Celery tasks with async code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.outreach_tasks.send_outreach_email_task")
def send_outreach_email_task(prospect_id: int, campaign_id: int, step: int):
    """Send a specific outreach email to a prospect."""
    return _run_async(_send_single_email(prospect_id, campaign_id, step))


async def _send_single_email(prospect_id: int, campaign_id: int, step: int) -> dict:
    """Send one email to one prospect."""
    async with async_session() as session:
        prospect = await session.get(Prospect, prospect_id)
        if not prospect or not prospect.email:
            return {"status": "skipped", "reason": "no email"}

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

        brevo = BrevoClient()
        result = brevo.send_email(
            to_email=email.to_email,
            to_name=email.to_name,
            subject=email.subject,
            html_content=email.html_content,
            tags=email.tags,
        )

        # Record event
        from datetime import datetime
        event = CampaignEvent(
            campaign_id=campaign_id,
            prospect_id=prospect_id,
            step=step,
            email_status=EmailStatus.SENT if result.success else EmailStatus.BOUNCED,
            sent_at=datetime.utcnow() if result.success else None,
            brevo_message_id=result.message_id,
        )
        session.add(event)
        await session.commit()

        return {
            "prospect_id": prospect_id,
            "step": step,
            "success": result.success,
            "message_id": result.message_id,
        }


@celery_app.task(name="app.workers.outreach_tasks.process_outreach_queue")
def process_outreach_queue():
    """Process pending outreach: send initial emails and follow-up reminders.

    Called every 30 minutes by Celery Beat.
    """
    return _run_async(_process_queue())


async def _process_queue() -> dict:
    """Run the outreach queue processor."""
    async with async_session() as session:
        results = await process_outreach(session)
        logger.info(f"Outreach queue processed: {results}")
        return results
