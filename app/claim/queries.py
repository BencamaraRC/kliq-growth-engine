"""Database queries for the claim flow."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cms.models import CMSUser, Page, Product
from app.db.models import GeneratedContent, OnboardingProgress, Prospect


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


# ─── Onboarding Progress Queries ─────────────────────────────────────────────

ONBOARDING_STEPS = ["password_set", "store_explored", "content_reviewed", "stripe_connected", "first_share"]


async def get_or_create_onboarding(session: AsyncSession, prospect_id: int) -> OnboardingProgress:
    """Get or create an onboarding progress record for a prospect."""
    result = await session.execute(
        select(OnboardingProgress).where(OnboardingProgress.prospect_id == prospect_id)
    )
    progress = result.scalar_one_or_none()
    if not progress:
        progress = OnboardingProgress(prospect_id=prospect_id)
        session.add(progress)
        await session.flush()
    return progress


async def get_onboarding_dict(session: AsyncSession, prospect_id: int) -> dict:
    """Get onboarding progress as a serializable dict."""
    progress = await get_or_create_onboarding(session, prospect_id)
    return {
        "prospect_id": progress.prospect_id,
        "password_set": progress.password_set,
        "store_explored": progress.store_explored,
        "content_reviewed": progress.content_reviewed,
        "stripe_connected": progress.stripe_connected,
        "first_share": progress.first_share,
        "progress_pct": progress.progress_pct,
        "started_at": progress.started_at.isoformat() if progress.started_at else None,
        "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
    }


async def complete_onboarding_step(session: AsyncSession, prospect_id: int, step_name: str) -> dict:
    """Mark an onboarding step as done, recalculate progress percentage.

    Returns updated onboarding dict.
    """
    if step_name not in ONBOARDING_STEPS:
        raise ValueError(f"Invalid onboarding step: {step_name}")

    progress = await get_or_create_onboarding(session, prospect_id)
    setattr(progress, step_name, True)

    # Recalculate percentage
    completed = sum(1 for s in ONBOARDING_STEPS if getattr(progress, s))
    progress.progress_pct = int((completed / len(ONBOARDING_STEPS)) * 100)

    if progress.progress_pct == 100 and not progress.completed_at:
        progress.completed_at = datetime.utcnow()

    await session.commit()
    return await get_onboarding_dict(session, prospect_id)


async def get_incomplete_onboarding_prospects(session: AsyncSession, claimed_before: datetime) -> list:
    """Find prospects with incomplete onboarding who claimed before a cutoff date."""
    result = await session.execute(
        select(OnboardingProgress, Prospect)
        .join(Prospect, OnboardingProgress.prospect_id == Prospect.id)
        .where(
            OnboardingProgress.progress_pct < 100,
            Prospect.status == "CLAIMED",
            Prospect.claimed_at <= claimed_before,
        )
    )
    return result.all()


async def get_store_pages(cms_db: AsyncSession, application_id: int) -> list[dict]:
    """Fetch CMS pages for the content review page."""
    result = await cms_db.execute(
        select(Page).where(
            Page.application_id == application_id,
            Page.deleted_at.is_(None),
        )
    )
    pages = result.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": (p.description or "")[:150],
            "page_type_id": p.page_type_id,
            "status_id": p.status_id,
            "media_url": p.media_url,
        }
        for p in pages
    ]


async def get_store_products(cms_db: AsyncSession, application_id: int) -> list[dict]:
    """Fetch CMS products for the content review page."""
    result = await cms_db.execute(
        select(Product).where(
            Product.application_id == application_id,
            Product.deleted_at.is_(None),
        )
    )
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "description": (p.description or "")[:150],
            "unit_amount": p.unit_amount,
            "interval": p.interval,
            "status_id": p.status_id,
            "media_url": p.media_url,
        }
        for p in products
    ]
