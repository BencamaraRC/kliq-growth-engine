"""Celery tasks for AI content generation.

Orchestrates the full AI pipeline for a prospect:
1. Generate bio (from profile data)
2. Generate blogs (from video transcripts)
3. Analyze pricing (from competitor tiers)
4. Generate SEO metadata
5. Extract brand colors (from profile image)

All results are stored in the generated_content table.
"""

import asyncio
import json
import logging

from sqlalchemy import select

from app.ai.bio_generator import generate_bio
from app.ai.blog_generator import generate_blogs_batch
from app.ai.client import AIClient
from app.ai.pricing_analyzer import analyze_pricing
from app.ai.seo_generator import generate_seo
from app.db.models import GeneratedContent, Prospect, ScrapedContentRecord, ScrapedPricingRecord
from app.db.session import async_session
from app.scrapers.color_extractor import extract_colors_from_url
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Bridge sync Celery tasks with async code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.ai_tasks.generate_content_task", bind=True, max_retries=2)
def generate_content_task(self, prospect_id: int):
    """Generate all AI content for a prospect.

    This is the main Phase 2 task. It loads the prospect's scraped data,
    runs all AI generators, and stores results in generated_content.
    """
    try:
        result = _run_async(_generate_all_content(prospect_id))
        logger.info(f"AI content generation complete for prospect {prospect_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"AI content generation failed for prospect {prospect_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


async def _generate_all_content(prospect_id: int) -> dict:
    """Run all AI generators for a prospect."""
    client = AIClient()

    async with async_session() as session:
        # Load prospect
        prospect = await session.get(Prospect, prospect_id)
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")

        # Load scraped content
        content_result = await session.execute(
            select(ScrapedContentRecord).where(
                ScrapedContentRecord.prospect_id == prospect_id
            )
        )
        scraped_content = content_result.scalars().all()

        # Load scraped pricing
        pricing_result = await session.execute(
            select(ScrapedPricingRecord).where(
                ScrapedPricingRecord.prospect_id == prospect_id
            )
        )
        scraped_pricing = pricing_result.scalars().all()

        results = {"prospect_id": prospect_id, "generated": []}

        # 1. Generate Bio
        content_titles = [c.title for c in scraped_content if c.title]
        bio = await generate_bio(
            client=client,
            name=prospect.name,
            platform=prospect.primary_platform.value if prospect.primary_platform else "unknown",
            bio=prospect.bio or "",
            niche_tags=prospect.niche_tags or [],
            follower_count=prospect.follower_count or 0,
            content_count=len(scraped_content),
            content_titles=content_titles,
        )
        await _store_generated(session, prospect_id, "bio", bio.tagline, json.dumps({
            "tagline": bio.tagline,
            "short_bio": bio.short_bio,
            "long_bio": bio.long_bio,
            "specialties": bio.specialties,
            "coaching_style": bio.coaching_style,
        }))
        results["generated"].append("bio")

        # 2. Generate Blogs from video transcripts
        videos = [
            {
                "title": c.title or "",
                "transcript": c.body or "",
                "description": c.description or "",
                "view_count": c.view_count or 0,
                "url": c.url or "",
            }
            for c in scraped_content
            if c.content_type == "video" and c.body
        ]
        blogs = await generate_blogs_batch(
            client=client,
            coach_name=prospect.name,
            videos=videos,
            max_blogs=5,
        )
        for blog in blogs:
            await _store_generated(session, prospect_id, "blog", blog.blog_title, json.dumps({
                "excerpt": blog.excerpt,
                "body_html": blog.body_html,
                "tags": blog.tags,
                "seo_title": blog.seo_title,
                "seo_description": blog.seo_description,
                "source_video_url": blog.source_video_url,
            }))
        results["generated"].append(f"blogs({len(blogs)})")

        # 3. Analyze Pricing
        pricing_tiers = [
            {
                "tier_name": p.tier_name,
                "platform": p.platform.value if p.platform else "unknown",
                "price_amount": p.price_amount,
                "currency": p.currency or "USD",
                "interval": p.interval or "month",
                "description": p.description or "",
                "benefits": p.benefits or [],
                "member_count": p.member_count or 0,
            }
            for p in scraped_pricing
        ]
        content_types = list({c.content_type for c in scraped_content})
        pricing = await analyze_pricing(
            client=client,
            name=prospect.name,
            niche_tags=prospect.niche_tags or [],
            follower_count=prospect.follower_count or 0,
            pricing_tiers=pricing_tiers,
            content_types=content_types or ["videos", "blog posts"],
        )
        for product in pricing.products:
            await _store_generated(session, prospect_id, "product", product.name, json.dumps({
                "description": product.description,
                "type": product.type,
                "price_cents": product.price_cents,
                "currency": product.currency,
                "interval": product.interval,
                "features": product.features,
                "recommended": product.recommended,
            }))
        results["generated"].append(f"products({len(pricing.products)})")

        # 4. Generate SEO
        seo = await generate_seo(
            client=client,
            name=prospect.name,
            tagline=bio.tagline,
            specialties=bio.specialties,
            niche_tags=prospect.niche_tags or [],
            location=prospect.location or "",
            content_titles=content_titles[:10],
        )
        await _store_generated(session, prospect_id, "seo", seo.seo_title, json.dumps({
            "seo_title": seo.seo_title,
            "seo_description": seo.seo_description,
            "seo_keywords": seo.seo_keywords,
            "og_title": seo.og_title,
            "og_description": seo.og_description,
            "store_slug": seo.store_slug,
        }))
        results["generated"].append("seo")

        # 5. Extract Brand Colors
        colors = await extract_colors_from_url(prospect.profile_image_url or "")
        if colors:
            await _store_generated(session, prospect_id, "colors", "Brand Colors", json.dumps({
                "primary": colors.primary,
                "secondary": colors.secondary,
                "accent": colors.accent,
                "background": colors.background,
                "text": colors.text,
                "palette": colors.palette,
            }))
            results["generated"].append("colors")

        # Update prospect status
        from app.db.models import ProspectStatus
        prospect.status = ProspectStatus.CONTENT_GENERATED
        await session.commit()

        results["token_usage"] = client.usage_summary
        return results


async def _store_generated(
    session,
    prospect_id: int,
    content_type: str,
    title: str,
    body: str,
    source_content_id: int | None = None,
):
    """Store a generated content record."""
    record = GeneratedContent(
        prospect_id=prospect_id,
        content_type=content_type,
        title=title,
        body=body,
        source_content_id=source_content_id,
    )
    session.add(record)
    await session.flush()
