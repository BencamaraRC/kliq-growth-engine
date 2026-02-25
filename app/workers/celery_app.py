"""Celery application configuration."""

from celery import Celery
from celery.schedules import crontab

from app.config import settings

celery_app = Celery(
    "kliq_growth_engine",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.workers.scrape_tasks",
        "app.workers.ai_tasks",
        "app.workers.populate_tasks",
        "app.workers.outreach_tasks",
        "app.workers.pipeline_task",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,  # 5 min soft limit
    task_time_limit=600,  # 10 min hard limit
    broker_connection_retry_on_startup=True,
)

# Periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Run discovery every day at 6 AM UTC
    "daily-discovery": {
        "task": "app.workers.scrape_tasks.discover_coaches_task",
        "schedule": crontab(hour=6, minute=0),
        "kwargs": {
            "platforms": ["youtube"],
            "search_queries": [
                "fitness coach",
                "personal trainer",
                "wellness coach",
                "yoga instructor",
                "nutrition coach",
            ],
            "max_per_platform": 50,
        },
    },
    # Process outreach queue every 30 minutes
    "outreach-processor": {
        "task": "app.workers.outreach_tasks.process_outreach_queue",
        "schedule": crontab(minute="*/30"),
    },
}
