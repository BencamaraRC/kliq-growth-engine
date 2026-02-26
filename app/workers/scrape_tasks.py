"""Celery tasks for platform scraping."""

import asyncio
import logging

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async code in Celery worker (sync context)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.scrape_tasks.discover_coaches_task", bind=True)
def discover_coaches_task(
    self,
    platforms: list[str] | None = None,
    search_queries: list[str] | None = None,
    max_per_platform: int = 50,
):
    """Discover coaches across platforms and store in database."""
    return _run_async(
        _discover_coaches(platforms, search_queries, max_per_platform)
    )


async def _discover_coaches(
    platforms: list[str] | None,
    search_queries: list[str] | None,
    max_per_platform: int,
):
    from sqlalchemy import select

    from app.db.models import Platform as PlatformEnum
    from app.db.models import Prospect, ProspectStatus
    from app.db.session import async_session
    from app.scrapers.discovery import DiscoveryOrchestrator
    from app.scrapers.youtube import YouTubeAdapter

    # Build adapter list
    adapters = [YouTubeAdapter()]
    # Future: add SkoolAdapter(), PatreonAdapter(), etc.

    orchestrator = DiscoveryOrchestrator(adapters)

    queries = search_queries or [
        "fitness coach",
        "personal trainer",
        "wellness coach",
    ]

    prospects = await orchestrator.discover(
        search_queries=queries,
        platforms=platforms,
        max_per_platform=max_per_platform,
    )

    # Store in database
    created_count = 0
    async with async_session() as db:
        for prospect in prospects:
            # Check if already exists
            result = await db.execute(
                select(Prospect).where(
                    Prospect.primary_platform == prospect.primary_profile.platform,
                    Prospect.primary_platform_id == prospect.primary_profile.platform_id,
                )
            )
            existing = result.scalar_one_or_none()
            if existing:
                continue

            db_prospect = Prospect(
                status=ProspectStatus.DISCOVERED,
                name=prospect.name,
                email=prospect.email,
                first_name=prospect.first_name,
                last_name=prospect.last_name,
                primary_platform=PlatformEnum(prospect.primary_profile.platform.value),
                primary_platform_id=prospect.primary_profile.platform_id,
                primary_platform_url=f"https://youtube.com/channel/{prospect.primary_profile.platform_id}",
                bio=prospect.bio,
                profile_image_url=prospect.profile_image_url,
                banner_image_url=prospect.primary_profile.banner_image_url,
                website_url=prospect.primary_profile.website_url,
                social_links=prospect.social_links,
                niche_tags=prospect.primary_profile.niche_tags,
                follower_count=prospect.primary_profile.follower_count,
                subscriber_count=prospect.primary_profile.subscriber_count,
                content_count=len(prospect.all_content),
                brand_colors=prospect.brand_colors,
            )
            db.add(db_prospect)
            created_count += 1

        await db.commit()

    # Log events
    from app.events.bigquery import log_event
    for prospect in prospects[:created_count]:
        log_event(
            "prospect_discovered",
            platform=prospect.primary_profile.platform.value,
        )

    logger.info(f"Discovery complete: {created_count} new prospects stored")
    return {"discovered": len(prospects), "new": created_count}


@celery_app.task(name="app.workers.scrape_tasks.scrape_single_coach_task", bind=True)
def scrape_single_coach_task(self, platform: str, platform_id: str):
    """Scrape a single coach from a specific platform."""
    return _run_async(_scrape_single(platform, platform_id))


async def _scrape_single(platform: str, platform_id: str):
    from app.db.models import Platform as PlatformEnum
    from app.db.models import Prospect, ProspectStatus, ScrapedContentRecord
    from app.db.session import async_session
    from app.scrapers.discovery import DiscoveryOrchestrator
    from app.scrapers.youtube import YouTubeAdapter

    adapters = [YouTubeAdapter()]
    orchestrator = DiscoveryOrchestrator(adapters)

    prospect = await orchestrator.scrape_single(platform, platform_id)

    async with async_session() as db:
        db_prospect = Prospect(
            status=ProspectStatus.SCRAPED,
            name=prospect.name,
            email=prospect.email,
            first_name=prospect.first_name,
            last_name=prospect.last_name,
            primary_platform=PlatformEnum(prospect.primary_profile.platform.value),
            primary_platform_id=prospect.primary_profile.platform_id,
            bio=prospect.bio,
            profile_image_url=prospect.profile_image_url,
            website_url=prospect.primary_profile.website_url,
            social_links=prospect.social_links,
            niche_tags=prospect.primary_profile.niche_tags,
            follower_count=prospect.primary_profile.follower_count,
            subscriber_count=prospect.primary_profile.subscriber_count,
            content_count=len(prospect.all_content),
            brand_colors=prospect.brand_colors,
        )
        db.add(db_prospect)
        await db.flush()

        for content in prospect.all_content:
            db_content = ScrapedContentRecord(
                prospect_id=db_prospect.id,
                platform=PlatformEnum(content.platform.value),
                content_type=content.content_type,
                title=content.title,
                description=content.description,
                body=content.body,
                url=content.url,
                thumbnail_url=content.thumbnail_url,
                published_at=content.published_at,
                view_count=content.view_count,
                engagement_count=content.engagement_count,
                tags=content.tags,
                raw_data=content.raw_data,
            )
            db.add(db_content)

        await db.commit()

    return {"prospect_id": db_prospect.id, "content_count": len(prospect.all_content)}
