"""Full pipeline orchestration task.

Chains: scrape → AI generate → populate store → outreach
"""

import asyncio
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

    The scraping should already be done before this task is called.
    """
    from app.workers.ai_tasks import generate_content_task
    from app.workers.populate_tasks import create_store_task

    pipeline = chain(
        generate_content_task.si(prospect_id=prospect_id),
        create_store_task.si(prospect_id=prospect_id),
    )

    result = pipeline.apply_async()
    logger.info(f"Full pipeline started for prospect {prospect_id}: {result.id}")
    return {"prospect_id": prospect_id, "chain_id": result.id}


@celery_app.task(name="app.workers.pipeline_task.scrape_and_pipeline_task")
def scrape_and_pipeline_task(prospect_id: int):
    """Scrape an existing prospect, then run full pipeline (AI + store).

    Chains: scrape_prospect → generate_content → create_store
    """
    from app.workers.ai_tasks import generate_content_task
    from app.workers.populate_tasks import create_store_task
    from app.workers.scrape_tasks import scrape_prospect_task

    pipeline = chain(
        scrape_prospect_task.si(prospect_id=prospect_id),
        generate_content_task.si(prospect_id=prospect_id),
        create_store_task.si(prospect_id=prospect_id),
    )

    result = pipeline.apply_async()
    logger.info(f"Scrape+pipeline started for prospect {prospect_id}: {result.id}")
    return {"prospect_id": prospect_id, "chain_id": result.id}


@celery_app.task(name="app.workers.pipeline_task.batch_pipeline_task")
def batch_pipeline_task(status_filter: str = "DISCOVERED"):
    """Run the full pipeline for all prospects with the given status.

    Dispatches individual scrape_and_pipeline chains for each prospect.
    Processes sequentially to avoid overwhelming APIs.
    """
    from app.db.session import async_session, engine, cms_engine
    from app.db.models import Prospect, ProspectStatus
    from sqlalchemy import select

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(engine.dispose())
        loop.run_until_complete(cms_engine.dispose())

        async def get_prospect_ids():
            async with async_session() as session:
                result = await session.execute(
                    select(Prospect.id).where(
                        Prospect.status == status_filter
                    ).order_by(Prospect.id)
                )
                return [row[0] for row in result.fetchall()]

        prospect_ids = loop.run_until_complete(get_prospect_ids())
    finally:
        loop.close()

    logger.info(f"Batch pipeline: {len(prospect_ids)} prospects with status={status_filter}")

    # Dispatch individual chains — Celery handles concurrency via prefetch
    dispatched = []
    for pid in prospect_ids:
        if status_filter == "DISCOVERED":
            task = scrape_and_pipeline_task.delay(prospect_id=pid)
        else:
            task = full_pipeline_task.delay(prospect_id=pid)
        dispatched.append({"prospect_id": pid, "task_id": task.id})
        logger.info(f"Dispatched pipeline for prospect {pid}: {task.id}")

    return {"dispatched": len(dispatched), "prospects": dispatched}
