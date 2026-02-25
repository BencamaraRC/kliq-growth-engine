"""Pipeline API routes — trigger scraping, AI generation, store creation."""

from pydantic import BaseModel
from fastapi import APIRouter

router = APIRouter()


class DiscoverRequest(BaseModel):
    """Trigger coach discovery on one or more platforms."""

    platforms: list[str] = ["youtube"]
    search_queries: list[str] = ["fitness coach", "personal trainer", "wellness coach"]
    max_per_platform: int = 50


class ScrapeRequest(BaseModel):
    """Scrape a specific coach from a platform."""

    platform: str
    platform_id: str


class PipelineRequest(BaseModel):
    """Run the full pipeline for a specific prospect."""

    prospect_id: int


class PipelineStatusResponse(BaseModel):
    task_id: str
    status: str


@router.post("/discover", response_model=PipelineStatusResponse)
async def trigger_discovery(request: DiscoverRequest):
    """Trigger coach discovery across platforms.

    This queues a Celery task that runs discovery, scraping, and
    stores results in the database.
    """
    from app.workers.scrape_tasks import discover_coaches_task

    task = discover_coaches_task.delay(
        platforms=request.platforms,
        search_queries=request.search_queries,
        max_per_platform=request.max_per_platform,
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/scrape", response_model=PipelineStatusResponse)
async def trigger_scrape(request: ScrapeRequest):
    """Scrape a single coach and run them through the full pipeline."""
    from app.workers.scrape_tasks import scrape_single_coach_task

    task = scrape_single_coach_task.delay(
        platform=request.platform,
        platform_id=request.platform_id,
    )
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.post("/run/{prospect_id}", response_model=PipelineStatusResponse)
async def trigger_full_pipeline(prospect_id: int):
    """Run the full pipeline (AI generation + store creation + outreach) for a prospect."""
    from app.workers.pipeline_task import full_pipeline_task

    task = full_pipeline_task.delay(prospect_id=prospect_id)
    return PipelineStatusResponse(task_id=task.id, status="queued")


@router.get("/status/{task_id}", response_model=PipelineStatusResponse)
async def get_task_status(task_id: str):
    """Check the status of an async pipeline task."""
    from app.workers.celery_app import celery_app

    result = celery_app.AsyncResult(task_id)
    return PipelineStatusResponse(task_id=task_id, status=result.status)
