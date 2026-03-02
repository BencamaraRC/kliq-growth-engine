"""Cloud Scheduler trigger endpoints.

These replace Celery Beat in production. Cloud Scheduler sends POST requests
to these endpoints on a cron schedule, and each endpoint enqueues the
corresponding Celery task.
"""

from fastapi import APIRouter, Header, HTTPException

from app.config import settings

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
