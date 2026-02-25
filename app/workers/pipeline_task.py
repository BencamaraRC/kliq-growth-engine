"""Full pipeline orchestration task.

Chains: scrape → AI generate → populate store → outreach
"""

import logging

from celery import chain

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.pipeline_task.full_pipeline_task")
def full_pipeline_task(prospect_id: int):
    """Run the full pipeline for a single prospect.

    Chains the tasks in order:
    1. AI content generation
    2. CMS store population
    3. Outreach email (step 1: "your store is ready")

    The scraping should already be done before this task is called.
    """
    from app.workers.ai_tasks import generate_content_task
    from app.workers.outreach_tasks import send_outreach_email_task
    from app.workers.populate_tasks import create_store_task

    pipeline = chain(
        generate_content_task.si(prospect_id=prospect_id),
        create_store_task.si(prospect_id=prospect_id),
        # Outreach is triggered after store creation completes
        # Campaign ID will be set by the pipeline orchestrator
    )

    result = pipeline.apply_async()
    logger.info(f"Full pipeline started for prospect {prospect_id}: {result.id}")
    return {"prospect_id": prospect_id, "chain_id": result.id}
