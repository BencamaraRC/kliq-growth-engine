"""Celery tasks for email outreach (Phase 4 — stubs for now)."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.outreach_tasks.send_outreach_email_task")
def send_outreach_email_task(prospect_id: int, campaign_id: int, step: int):
    """Send an outreach email to a prospect.

    TODO (Phase 4): Implement
    - Build personalized email from template
    - Send via Brevo API
    - Track delivery in campaign_events
    """
    logger.info(f"[STUB] Outreach email for prospect {prospect_id}, step {step}")
    return {"prospect_id": prospect_id, "step": step, "status": "stub"}


@celery_app.task(name="app.workers.outreach_tasks.process_outreach_queue")
def process_outreach_queue():
    """Process pending outreach: send follow-ups, handle timing.

    TODO (Phase 4): Implement
    - Check for prospects with created stores but no email sent
    - Check for opened-but-unclaimed stores due for reminder
    - Queue individual send tasks
    """
    logger.info("[STUB] Processing outreach queue")
    return {"status": "stub"}
