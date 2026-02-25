"""Celery tasks for AI content generation (Phase 2 — stubs for now)."""

import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.workers.ai_tasks.generate_content_task")
def generate_content_task(prospect_id: int):
    """Generate all AI content for a prospect.

    TODO (Phase 2): Implement
    - Bio generation (bio_generator.py)
    - Blog generation from transcripts (blog_generator.py)
    - Pricing analysis (pricing_analyzer.py)
    - SEO metadata (seo_generator.py)
    - Color extraction (color_extractor.py)
    """
    logger.info(f"[STUB] AI content generation for prospect {prospect_id}")
    return {"prospect_id": prospect_id, "status": "stub"}
