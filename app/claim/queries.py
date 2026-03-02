"""Database queries for the claim flow."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cms.models import CMSUser
from app.db.models import GeneratedContent, Prospect


async def get_prospect_by_token(session: AsyncSession, token: str) -> dict | None:
    """Fetch a prospect by claim_token and return as a dict, or None."""
    result = await session.execute(
        select(Prospect).where(Prospect.claim_token == token)
    )
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
        "niche_tags": prospect.niche_tags,
        "brand_colors": prospect.brand_colors,
        "primary_platform": prospect.primary_platform.value if prospect.primary_platform else None,
        "status": prospect.status.value if prospect.status else None,
        "claim_token": prospect.claim_token,
        "kliq_store_url": prospect.kliq_store_url,
        "kliq_application_id": prospect.kliq_application_id,
    }


async def get_auto_login_token(cms_db: AsyncSession, prospect: dict) -> str | None:
    """Fetch the auto-login token for a prospect from the CMS users table."""
    app_id = prospect.get("kliq_application_id")
    email = prospect.get("email")
    if not app_id or not email:
        return None
    result = await cms_db.execute(
        select(CMSUser.auto_login_token).where(
            CMSUser.application_id == app_id,
            CMSUser.email == email,
        )
    )
    return result.scalar_one_or_none()


async def get_content_counts(session: AsyncSession, prospect_id: int) -> dict:
    """Get counts of generated content types for a prospect."""
    result = await session.execute(
        select(GeneratedContent).where(GeneratedContent.prospect_id == prospect_id)
    )
    rows = result.scalars().all()
    blog_count = sum(1 for r in rows if r.content_type == "blog")
    product_count = sum(1 for r in rows if r.content_type == "product")
    return {"blog_count": blog_count, "product_count": product_count}
