"""Celery tasks for CMS webstore population (Phase 3 — stubs for now)."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.populate_tasks.create_store_task")
def create_store_task(prospect_id: int):
    """Create a KLIQ webstore for a prospect.

    TODO (Phase 3): Implement
    - Direct MySQL writes to RCWL-CMS database
    - Application + Setting + Color + FeatureSetup creation
    - Coach user creation (type=3)
    - Product, Post, Page creation (all Draft)
    - S3 media upload
    """
    logger.info(f"[STUB] Store creation for prospect {prospect_id}")
    return {"prospect_id": prospect_id, "status": "stub"}
