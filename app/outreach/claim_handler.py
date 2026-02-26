"""Store claim flow — handles coach claiming their pre-built KLIQ store.

When a coach clicks "Claim Your Store" from an outreach email:
1. Validate the claim token
2. Set their chosen password in the CMS
3. Activate the store (status 1 → 2 in CMS)
4. Update prospect status to CLAIMED
5. Send claim confirmation email
"""

import logging
from datetime import datetime

import bcrypt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.cms.models import Application, ApplicationSetting, CMSUser
from app.cms.store_builder import STATUS_ACTIVE, STATUS_INACTIVE
from app.db.models import Prospect, ProspectStatus

logger = logging.getLogger(__name__)


class ClaimError(Exception):
    """Error during store claim process."""
    pass


async def validate_claim_token(growth_db: AsyncSession, token: str) -> Prospect:
    """Validate a claim token and return the associated prospect.

    Raises:
        ClaimError: If token is invalid or store already claimed.
    """
    result = await growth_db.execute(
        select(Prospect).where(Prospect.claim_token == token)
    )
    prospect = result.scalar_one_or_none()

    if not prospect:
        raise ClaimError("Invalid claim token")

    if prospect.status == ProspectStatus.CLAIMED:
        raise ClaimError("Store already claimed")

    if not prospect.kliq_application_id:
        raise ClaimError("No store associated with this claim")

    return prospect


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
    4. Update prospect status → CLAIMED

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

    # 1. Activate the CMS user
    await cms_db.execute(
        update(CMSUser).where(
            CMSUser.application_id == app_id,
            CMSUser.email == prospect.email,
        ).values(
            password=hashed_password,
            status_id=STATUS_ACTIVE,
            is_email_verified=True,
        )
    )

    # 2. Activate the application
    await cms_db.execute(
        update(Application).where(
            Application.id == app_id,
        ).values(
            status_id=STATUS_ACTIVE,
        )
    )

    await cms_db.commit()

    # 3. Update prospect in Growth DB
    prospect.status = ProspectStatus.CLAIMED
    prospect.claimed_at = datetime.utcnow()
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
    }
