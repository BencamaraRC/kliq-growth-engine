"""Cloud Scheduler trigger endpoints.

These replace Celery Beat in production. Cloud Scheduler sends POST requests
to these endpoints on a cron schedule, and each endpoint enqueues the
corresponding Celery task.
"""

from fastapi import APIRouter, Header, HTTPException
from sqlalchemy import select

from app.config import settings
from app.db.models import Prospect
from app.db.session import get_db

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


def _verify_secret(x_scheduler_secret: str = Header(...)):
    if not settings.scheduler_secret:
        raise HTTPException(status_code=503, detail="Scheduler secret not configured")
    if x_scheduler_secret != settings.scheduler_secret:
        raise HTTPException(status_code=403, detail="Invalid scheduler secret")


@router.post("/discovery")
async def trigger_discovery(x_scheduler_secret: str = Header(...)):
    """Trigger daily coach discovery (replaces Beat daily-discovery)."""
    _verify_secret(x_scheduler_secret)

    from app.workers.scrape_tasks import discover_coaches_task

    task = discover_coaches_task.delay(
        platforms=["youtube"],
        search_queries=[
            "fitness coach",
            "personal trainer",
            "wellness coach",
            "yoga instructor",
            "nutrition coach",
            "business coach",
            "life coach",
            "marketing coach",
            "make money online coach",
            "online business mentor",
        ],
        max_per_platform=50,
    )
    return {"status": "enqueued", "task_id": task.id}


@router.post("/outreach")
async def trigger_outreach(x_scheduler_secret: str = Header(...)):
    """Trigger outreach queue processing (replaces Beat outreach-processor)."""
    _verify_secret(x_scheduler_secret)

    from app.workers.outreach_tasks import process_outreach_queue

    task = process_outreach_queue.delay()
    return {"status": "enqueued", "task_id": task.id}


@router.post("/onboarding")
async def trigger_onboarding(x_scheduler_secret: str = Header(...)):
    """Trigger onboarding email processing (replaces Beat onboarding-emails)."""
    _verify_secret(x_scheduler_secret)

    from app.workers.outreach_tasks import process_onboarding_emails_task

    task = process_onboarding_emails_task.delay()
    return {"status": "enqueued", "task_id": task.id}


@router.post("/test-send/{prospect_id}")
async def test_send_email(prospect_id: int, step: int = 1, x_scheduler_secret: str = Header(...)):
    """Send a test email directly (bypasses Celery). For testing only."""
    _verify_secret(x_scheduler_secret)

    from app.outreach.brevo_client import BrevoClient
    from app.outreach.campaign_manager import _send_step

    async for session in get_db():
        result = await session.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        prospect = result.scalar_one_or_none()
        if not prospect:
            raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
        if not prospect.email:
            raise HTTPException(status_code=400, detail="Prospect has no email")

        success = await _send_step(session, BrevoClient(), prospect, step=step)
        return {
            "status": "sent" if success else "failed",
            "prospect_id": prospect_id,
            "email": prospect.email,
            "step": step,
        }


@router.get("/debug/{prospect_id}")
async def debug_prospect(prospect_id: int, x_scheduler_secret: str = Header(...)):
    """Get full prospect details including claim_token. For testing only."""
    _verify_secret(x_scheduler_secret)

    async for session in get_db():
        result = await session.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        prospect = result.scalar_one_or_none()
        if not prospect:
            raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")

        return {
            "id": prospect.id,
            "name": prospect.name,
            "email": prospect.email,
            "status": prospect.status.value if prospect.status else None,
            "claim_token": prospect.claim_token,
            "kliq_application_id": prospect.kliq_application_id,
            "kliq_store_url": prospect.kliq_store_url,
            "primary_platform": prospect.primary_platform.value if prospect.primary_platform else None,
            "niche_tags": prospect.niche_tags,
            "first_name": prospect.first_name,
        }
