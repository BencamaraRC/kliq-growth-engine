"""Celery tasks for CMS webstore population.

Creates a complete KLIQ webstore from AI-generated content:
1. Build the store (Application + Settings + Colors + User + Roles)
2. Create products from pricing analysis
3. Create About page and blog pages from generated content
4. Upload media to S3
5. Update prospect record with store details
"""

import asyncio
import json
import logging
import secrets

from sqlalchemy import select

from app.ai.blog_generator import GeneratedBlog
from app.ai.pricing_analyzer import SuggestedProduct
from app.cms.content import create_about_page, create_blog_pages
from app.cms.media import upload_store_images
from app.cms.products import create_products
from app.cms.store_builder import build_store
from app.db.models import GeneratedContent, Prospect, ProspectStatus
from app.db.session import async_session, cms_session as cms_async_session
from app.scrapers.color_extractor import BrandColors
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Bridge sync Celery tasks with async code."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(name="app.workers.populate_tasks.create_store_task", bind=True, max_retries=1)
def create_store_task(self, prospect_id: int):
    """Create a KLIQ webstore for a prospect.

    Reads AI-generated content from the growth DB, then writes to the
    CMS MySQL database to build the complete store.
    """
    try:
        result = _run_async(_create_store(prospect_id))
        logger.info(f"Store creation complete for prospect {prospect_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"Store creation failed for prospect {prospect_id}: {exc}")
        raise self.retry(exc=exc, countdown=120)


async def _create_store(prospect_id: int) -> dict:
    """Full store creation flow."""

    # 1. Load prospect and generated content from Growth DB
    async with async_session() as growth_db:
        prospect = await growth_db.get(Prospect, prospect_id)
        if not prospect:
            raise ValueError(f"Prospect {prospect_id} not found")

        gen_result = await growth_db.execute(
            select(GeneratedContent).where(GeneratedContent.prospect_id == prospect_id)
        )
        generated = gen_result.scalars().all()

    # Parse generated content by type
    bio_data = _find_generated(generated, "bio")
    seo_data = _find_generated(generated, "seo")
    colors_data = _find_generated(generated, "colors")
    product_records = [g for g in generated if g.content_type == "product"]
    blog_records = [g for g in generated if g.content_type == "blog"]

    # Build brand colors
    brand_colors = None
    if colors_data:
        c = json.loads(colors_data.body)
        brand_colors = BrandColors(
            primary=c.get("primary", "#1E81FF"),
            secondary=c.get("secondary", "#1A74E5"),
            accent=c.get("accent", "#1E81FF"),
            background=c.get("background", "#FFFFFF"),
            text=c.get("text", "#1A1A1A"),
            palette=c.get("palette", []),
        )

    # Parse SEO
    seo = json.loads(seo_data.body) if seo_data else {}

    # Parse bio
    bio = json.loads(bio_data.body) if bio_data else {}

    # Determine names
    first_name = prospect.first_name or prospect.name.split()[0]
    last_name = prospect.last_name or (prospect.name.split()[1] if len(prospect.name.split()) > 1 else "")

    # 2. Create store in CMS MySQL
    async with cms_async_session() as cms_db:
        store = await build_store(
            session=cms_db,
            name=prospect.name,
            email=prospect.email or f"unclaimed-{prospect_id}@joinkliq.io",
            first_name=first_name,
            last_name=last_name,
            coach_name=prospect.name,
            brand_colors=brand_colors,
            seo_title=seo.get("seo_title"),
            seo_description=seo.get("seo_description"),
            seo_keywords=", ".join(seo.get("seo_keywords", [])),
            store_slug=seo.get("store_slug"),
            profile_image_url=prospect.profile_image_url,
            support_email=prospect.email,
        )

        # 3. Create products
        products = []
        for pr in product_records:
            p = json.loads(pr.body)
            products.append(SuggestedProduct(
                name=pr.title or p.get("name", ""),
                description=p.get("description", ""),
                type=p.get("type", "subscription"),
                price_cents=p.get("price_cents", 999),
                currency=p.get("currency", "USD"),
                interval=p.get("interval"),
                features=p.get("features", []),
                recommended=p.get("recommended", False),
            ))

        product_ids = []
        if products:
            product_ids = await create_products(cms_db, store.application_id, products)

        # 4. Create pages
        page_ids = []

        # About page
        if bio.get("long_bio"):
            about_id = await create_about_page(
                cms_db,
                store.application_id,
                long_bio=bio["long_bio"],
                tagline=bio.get("tagline", ""),
                profile_image_url=prospect.profile_image_url,
            )
            page_ids.append(about_id)

        # Blog pages
        blogs = []
        for br in blog_records:
            b = json.loads(br.body)
            if b.get("body_html"):
                blogs.append(GeneratedBlog(
                    blog_title=br.title or b.get("blog_title", ""),
                    excerpt=b.get("excerpt", ""),
                    body_html=b.get("body_html", ""),
                    tags=b.get("tags", []),
                    seo_title=b.get("seo_title", ""),
                    seo_description=b.get("seo_description", ""),
                    source_video_url=b.get("source_video_url", ""),
                ))

        if blogs:
            blog_ids = await create_blog_pages(cms_db, store.application_id, blogs)
            page_ids.extend(blog_ids)

        await cms_db.commit()

    # 5. Upload media to S3
    media = await upload_store_images(
        application_id=store.application_id,
        profile_image_url=prospect.profile_image_url,
        banner_image_url=prospect.banner_image_url,
    )

    # 6. Update prospect in Growth DB
    claim_token = secrets.token_urlsafe(32)
    async with async_session() as growth_db:
        prospect = await growth_db.get(Prospect, prospect_id)
        prospect.kliq_application_id = store.application_id
        prospect.kliq_store_url = store.store_url
        prospect.claim_token = claim_token
        prospect.status = ProspectStatus.STORE_CREATED
        from datetime import datetime
        prospect.store_created_at = datetime.utcnow()
        await growth_db.commit()

    return {
        "prospect_id": prospect_id,
        "application_id": store.application_id,
        "store_url": store.store_url,
        "user_id": store.user_id,
        "products_created": len(product_ids),
        "pages_created": len(page_ids),
        "media_uploaded": {k: v is not None for k, v in media.items()},
        "claim_token": claim_token,
    }


def _find_generated(records: list, content_type: str):
    """Find the first generated content record of a given type."""
    for r in records:
        if r.content_type == content_type:
            return r
    return None
