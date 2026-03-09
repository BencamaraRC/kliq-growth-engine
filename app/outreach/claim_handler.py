"""Store claim flow — handles coach claiming their pre-built KLIQ store.

When a coach clicks "Claim Your Store" from an outreach email:
1. Validate the claim token
2. Set their chosen password in the CMS
3. Activate the store (status 1 → 2 in CMS)
4. Update prospect status to CLAIMED
5. Send claim confirmation email
"""

import logging
import secrets
from datetime import datetime, timedelta

import bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cms.models import Application, CMSUser, Page, Product
from app.cms.store_builder import STATUS_ACTIVE, STATUS_INACTIVE
from app.db.models import OnboardingProgress, Prospect, ProspectStatus

logger = logging.getLogger(__name__)


class ClaimError(Exception):
    """Error during store claim process."""

    pass


async def validate_claim_token(growth_db: AsyncSession, token: str) -> Prospect:
    """Validate a claim token and return the associated prospect.

    Raises:
        ClaimError: If token is invalid or store already claimed.
    """
    result = await growth_db.execute(select(Prospect).where(Prospect.claim_token == token))
    prospect = result.scalar_one_or_none()

    if not prospect:
        raise ClaimError("Invalid claim token")

    if prospect.status == ProspectStatus.CLAIMED:
        raise ClaimError("Store already claimed")

    if not prospect.kliq_application_id:
        raise ClaimError("No store associated with this claim")

    return prospect


async def activate_store_content(cms_db: AsyncSession, application_id: int) -> int:
    """Activate all pages and products for a store (status 1 → 2).

    Called during claim so the coach's store is live immediately.
    Returns the number of rows updated.
    """
    try:
        pages_result = await cms_db.execute(
            update(Page)
            .where(
                Page.application_id == application_id,
                Page.status_id == STATUS_INACTIVE,
                Page.deleted_at.is_(None),
            )
            .values(status_id=STATUS_ACTIVE)
        )
        products_result = await cms_db.execute(
            update(Product)
            .where(
                Product.application_id == application_id,
                Product.status_id == STATUS_INACTIVE,
                Product.deleted_at.is_(None),
            )
            .values(status_id=STATUS_ACTIVE)
        )
        total = (pages_result.rowcount or 0) + (products_result.rowcount or 0)
        logger.info(f"Activated {total} pages/products for app {application_id}")
        return total
    except Exception:
        logger.exception(f"Failed to activate content for app {application_id}")
        return 0


async def activate_store(
    cms_db: AsyncSession,
    growth_db: AsyncSession,
    prospect: Prospect,
    password: str,
) -> dict:
    """Activate a claimed store in the CMS.

    1. Hash the new password
    2. Update CMS user password and status → Active
    3. Update CMS application status → Active
    4. Activate all pages/products (draft → published)
    5. Update prospect status → CLAIMED
    6. Create OnboardingProgress with password_set=True

    Args:
        cms_db: CMS MySQL session.
        growth_db: Growth Engine PostgreSQL session.
        prospect: The prospect claiming the store.
        password: The coach's chosen password.

    Returns:
        Dict with activation details.
    """
    app_id = prospect.kliq_application_id
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Generate one-time auto-login token (30-minute expiry)
    auto_login_token = secrets.token_hex(64)
    auto_login_expires = datetime.utcnow() + timedelta(minutes=30)

    # 1. Activate the CMS user (match by application_id; email may be a placeholder)
    user_updates = {
        "password": hashed_password,
        "status_id": STATUS_ACTIVE,
        "is_email_verified": True,
        "auto_login_token": auto_login_token,
        "auto_login_token_expires_at": auto_login_expires,
    }
    if prospect.email:
        user_updates["email"] = prospect.email
    await cms_db.execute(
        update(CMSUser)
        .where(CMSUser.application_id == app_id)
        .values(**user_updates)
    )

    # 2. Activate the application
    await cms_db.execute(
        update(Application)
        .where(
            Application.id == app_id,
        )
        .values(
            status_id=STATUS_ACTIVE,
        )
    )

    # 3. Activate all store content (pages + products)
    await activate_store_content(cms_db, app_id)

    await cms_db.commit()

    # 4. Update prospect in Growth DB
    prospect.status = ProspectStatus.CLAIMED
    prospect.claimed_at = datetime.utcnow()

    # 5. Create or update onboarding progress with password_set=True
    existing_onboarding = await growth_db.execute(
        select(OnboardingProgress).where(OnboardingProgress.prospect_id == prospect.id)
    )
    onboarding = existing_onboarding.scalar_one_or_none()
    if onboarding:
        onboarding.password_set = True
        onboarding.progress_pct = 25
    else:
        onboarding = OnboardingProgress(
            prospect_id=prospect.id,
            password_set=True,
            progress_pct=25,
        )
        growth_db.add(onboarding)

    await growth_db.commit()

    logger.info(f"Store {app_id} activated for {prospect.email}")

    # Log events and notify
    from app.events.bigquery import log_event
    from app.events.slack import notify_store_claimed

    log_event(
        "store_claimed",
        prospect_id=prospect.id,
        application_id=app_id,
    )
    log_event(
        "onboarding_started",
        prospect_id=prospect.id,
        application_id=app_id,
    )
    notify_store_claimed(
        prospect_name=prospect.name,
        email=prospect.email or "",
        platform=prospect.primary_platform.value if prospect.primary_platform else "unknown",
        application_id=app_id,
    )

    return {
        "application_id": app_id,
        "store_url": prospect.kliq_store_url,
        "email": prospect.email,
        "auto_login_token": auto_login_token,
    }
