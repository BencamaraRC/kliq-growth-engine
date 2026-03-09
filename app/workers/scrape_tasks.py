"""Celery tasks for platform scraping."""

import asyncio
import logging
from datetime import datetime

from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Run async code in Celery worker (sync context)."""
    from app.db.session import cms_engine, engine

    loop = asyncio.new_event_loop()
    try:
        # Dispose stale pools bound to previous event loops
        loop.run_until_complete(engine.dispose())
        loop.run_until_complete(cms_engine.dispose())
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
    return _run_async(_discover_coaches(platforms, search_queries, max_per_platform))


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
    from app.scrapers.stan import StanAdapter
    from app.scrapers.youtube import YouTubeAdapter

    # Build adapter list
    adapters = [YouTubeAdapter(), StanAdapter()]

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
    from app.scrapers.stan import StanAdapter
    from app.scrapers.youtube import YouTubeAdapter

    adapters = [YouTubeAdapter(), StanAdapter()]
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
                published_at=_parse_datetime(content.published_at),
                view_count=content.view_count,
                engagement_count=content.engagement_count,
                tags=content.tags,
                raw_data=content.raw_data,
            )
            db.add(db_content)

        await db.commit()

    return {"prospect_id": db_prospect.id, "content_count": len(prospect.all_content)}


@celery_app.task(name="app.workers.scrape_tasks.scrape_prospect_task", bind=True, max_retries=2)
def scrape_prospect_task(self, prospect_id: int):
    """Scrape an existing DISCOVERED prospect using their stored platform ID."""
    try:
        return _run_async(_scrape_existing_prospect(prospect_id))
    except Exception as exc:
        logger.error(f"Scrape failed for prospect {prospect_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


async def _scrape_existing_prospect(prospect_id: int):
    from app.db.models import Prospect, ProspectStatus, ScrapedContentRecord
    from app.db.session import async_session
    from app.scrapers.discovery import DiscoveryOrchestrator
    from app.scrapers.stan import StanAdapter
    from app.scrapers.youtube import YouTubeAdapter

    async with async_session() as db:
        prospect = await db.get(Prospect, prospect_id)
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")
        if prospect.status not in (ProspectStatus.DISCOVERED,):
            logger.info(f"Prospect {prospect_id} already {prospect.status.value}, skipping scrape")
            return {"prospect_id": prospect_id, "content_count": 0, "skipped": True}

        platform = prospect.primary_platform.value if prospect.primary_platform else "youtube"
        platform_id = prospect.primary_platform_id

        adapters = [YouTubeAdapter(), StanAdapter()]
        orchestrator = DiscoveryOrchestrator(adapters)
        scraped = await orchestrator.scrape_single(platform, platform_id)

        # Update existing prospect with scraped data
        prospect.bio = scraped.bio or prospect.bio
        prospect.profile_image_url = scraped.profile_image_url or prospect.profile_image_url
        prospect.banner_image_url = (
            scraped.primary_profile.banner_image_url or prospect.banner_image_url
        )
        prospect.website_url = scraped.primary_profile.website_url or prospect.website_url
        prospect.social_links = scraped.social_links or prospect.social_links
        prospect.niche_tags = scraped.primary_profile.niche_tags or prospect.niche_tags
        prospect.follower_count = scraped.primary_profile.follower_count or prospect.follower_count
        prospect.subscriber_count = (
            scraped.primary_profile.subscriber_count or prospect.subscriber_count
        )
        prospect.content_count = len(scraped.all_content)
        prospect.brand_colors = scraped.brand_colors or prospect.brand_colors
        prospect.first_name = scraped.first_name or prospect.first_name
        prospect.last_name = scraped.last_name or prospect.last_name
        prospect.email = scraped.email or prospect.email
        prospect.status = ProspectStatus.SCRAPED

        # Store scraped content records
        for content in scraped.all_content:
            db_content = ScrapedContentRecord(
                prospect_id=prospect_id,
                platform=prospect.primary_platform,
                content_type=content.content_type,
                title=content.title,
                description=content.description,
                body=content.body,
                url=content.url,
                thumbnail_url=content.thumbnail_url,
                published_at=_parse_datetime(content.published_at),
                view_count=content.view_count,
                engagement_count=content.engagement_count,
                tags=content.tags,
                raw_data=content.raw_data,
            )
            db.add(db_content)

        await db.commit()

    logger.info(f"Scraped prospect {prospect_id}: {len(scraped.all_content)} content items")
    return {"prospect_id": prospect_id, "content_count": len(scraped.all_content)}


def _parse_datetime(value) -> datetime | None:
    """Parse an ISO datetime string to a naive datetime object."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.replace(tzinfo=None)
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.replace(tzinfo=None)
    except (ValueError, AttributeError):
        return None
