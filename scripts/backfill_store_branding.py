"""Backfill existing stores with branding data from AI-generated content.

Updates ApplicationSetting and Application for all Growth Engine-created stores:
- Sets enable_new_home=True (redirects to /your-store)
- Populates shop_description from generated bio
- Populates logos from profile_image_url
- Sets copyright_text, enable_shop, default_image
- Writes S3 URLs if media was previously uploaded

Usage:
    python -m scripts.backfill_store_branding
"""

import asyncio
import json
import logging
from datetime import datetime

from sqlalchemy import select, update

from app.cms.models import Application, ApplicationSetting
from app.db.models import GeneratedContent, Prospect
from app.db.session import async_session, cms_engine, cms_session, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def backfill():
    """Backfill all existing stores with branding data."""
    # Dispose stale pools
    await engine.dispose()
    await cms_engine.dispose()

    # 1. Load all prospects with stores
    async with async_session() as growth_db:
        result = await growth_db.execute(
            select(Prospect).where(Prospect.kliq_application_id.isnot(None)).order_by(Prospect.id)
        )
        prospects = result.scalars().all()

    logger.info(f"Found {len(prospects)} prospects with stores to backfill")

    updated = 0
    for prospect in prospects:
        app_id = prospect.kliq_application_id

        # Load generated content
        async with async_session() as growth_db:
            gen_result = await growth_db.execute(
                select(GeneratedContent).where(GeneratedContent.prospect_id == prospect.id)
            )
            generated = gen_result.scalars().all()

        bio_record = next((g for g in generated if g.content_type == "bio"), None)
        bio = json.loads(bio_record.body) if bio_record else {}

        short_bio = bio.get("short_bio", "")
        profile_url = prospect.profile_image_url
        banner_url = prospect.banner_image_url

        # Update CMS
        async with cms_session() as cms_db:
            # Set enable_new_home on Application
            await cms_db.execute(
                update(Application)
                .where(Application.id == app_id)
                .values(enable_new_home=True)
            )

            # Update ApplicationSetting
            settings_result = await cms_db.execute(
                select(ApplicationSetting).where(ApplicationSetting.application_id == app_id)
            )
            app_settings = settings_result.scalars().first()

            if app_settings:
                if not app_settings.default_image:
                    app_settings.default_image = banner_url or profile_url
                if not app_settings.shop_description:
                    app_settings.shop_description = short_bio
                if not app_settings.shop_image:
                    app_settings.shop_image = profile_url
                if not app_settings.light_home_logo:
                    app_settings.light_home_logo = profile_url
                if not app_settings.dark_home_logo:
                    app_settings.dark_home_logo = profile_url
                if not app_settings.light_login_logo:
                    app_settings.light_login_logo = profile_url
                if not app_settings.dark_login_logo:
                    app_settings.dark_login_logo = profile_url
                if not app_settings.copyright_text:
                    app_settings.copyright_text = f"\u00a9 {datetime.now().year} {prospect.name}. All rights reserved."
                if not app_settings.favicon:
                    app_settings.favicon = profile_url
                app_settings.enable_shop = True

            await cms_db.commit()

        updated += 1
        logger.info(f"  [{updated}/{len(prospects)}] Updated store {app_id} for {prospect.name}")

    logger.info(f"Backfill complete: {updated} stores updated")


if __name__ == "__main__":
    asyncio.run(backfill())
