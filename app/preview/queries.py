"""Database queries for the public store preview route."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GeneratedContent, Prospect


async def get_prospect_by_token(session: AsyncSession, token: str) -> dict | None:
    """Fetch a prospect by claim_token and return as a dict, or None."""
    result = await session.execute(select(Prospect).where(Prospect.claim_token == token))
    prospect = result.scalar_one_or_none()
    if not prospect:
        return None
    return {
        "id": prospect.id,
        "name": prospect.name,
        "email": prospect.email,
        "first_name": prospect.first_name,
        "last_name": prospect.last_name,
        "bio": prospect.bio,
        "profile_image_url": prospect.profile_image_url,
        "banner_image_url": prospect.banner_image_url,
        "niche_tags": prospect.niche_tags,
        "brand_colors": prospect.brand_colors,
        "primary_platform": prospect.primary_platform.value if prospect.primary_platform else None,
        "status": prospect.status.value if prospect.status else None,
        "claim_token": prospect.claim_token,
        "kliq_store_url": prospect.kliq_store_url,
        "kliq_application_id": prospect.kliq_application_id,
    }


async def get_generated_content(session: AsyncSession, prospect_id: int) -> list[dict]:
    """Fetch all generated content rows for a prospect as a list of dicts."""
    result = await session.execute(
        select(GeneratedContent).where(GeneratedContent.prospect_id == prospect_id)
    )
    rows = result.scalars().all()
    return [
        {
            "content_type": row.content_type,
            "title": row.title,
            "body": row.body,
        }
        for row in rows
    ]
