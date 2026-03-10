"""Cloud Scheduler trigger endpoints.

These replace Celery Beat in production. Cloud Scheduler sends POST requests
to these endpoints on a cron schedule, and each endpoint enqueues the
corresponding Celery task.
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Prospect
from app.db.session import get_cms_db, get_db

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


def _verify_secret(x_scheduler_secret: str = Header(...)):
    if not settings.scheduler_secret:
        raise HTTPException(status_code=503, detail="Scheduler secret not configured")
    if x_scheduler_secret != settings.scheduler_secret:
        raise HTTPException(status_code=403, detail="Invalid scheduler secret")


@router.post("/discovery")
async def trigger_discovery(x_scheduler_secret: str = Header(...)):
    """Trigger daily coach discovery (replaces Beat daily-discovery)."""
    _verify_secret(x_scheduler_secret)

    from app.workers.scrape_tasks import discover_coaches_task

    task = discover_coaches_task.delay(
        platforms=["youtube"],
        search_queries=[
            "fitness coach",
            "personal trainer",
            "wellness coach",
            "yoga instructor",
            "nutrition coach",
            "business coach",
            "life coach",
            "marketing coach",
            "make money online coach",
            "online business mentor",
        ],
        max_per_platform=50,
    )
    return {"status": "enqueued", "task_id": task.id}


@router.post("/outreach")
async def trigger_outreach(x_scheduler_secret: str = Header(...)):
    """Trigger outreach queue processing (replaces Beat outreach-processor)."""
    _verify_secret(x_scheduler_secret)

    from app.workers.outreach_tasks import process_outreach_queue

    task = process_outreach_queue.delay()
    return {"status": "enqueued", "task_id": task.id}


@router.post("/onboarding")
async def trigger_onboarding(x_scheduler_secret: str = Header(...)):
    """Trigger onboarding email processing (replaces Beat onboarding-emails)."""
    _verify_secret(x_scheduler_secret)

    from app.workers.outreach_tasks import process_onboarding_emails_task

    task = process_onboarding_emails_task.delay()
    return {"status": "enqueued", "task_id": task.id}


@router.post("/test-send/{prospect_id}")
async def test_send_email(prospect_id: int, step: int = 1, x_scheduler_secret: str = Header(...)):
    """Send a test email directly (bypasses Celery). For testing only."""
    _verify_secret(x_scheduler_secret)

    from app.outreach.brevo_client import BrevoClient
    from app.outreach.campaign_manager import _send_step

    async for session in get_db():
        result = await session.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        prospect = result.scalar_one_or_none()
        if not prospect:
            raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")
        if not prospect.email:
            raise HTTPException(status_code=400, detail="Prospect has no email")

        success = await _send_step(session, BrevoClient(), prospect, step=step)
        return {
            "status": "sent" if success else "failed",
            "prospect_id": prospect_id,
            "email": prospect.email,
            "step": step,
        }


@router.get("/debug/{prospect_id}")
async def debug_prospect(prospect_id: int, x_scheduler_secret: str = Header(...)):
    """Get full prospect details including claim_token. For testing only."""
    _verify_secret(x_scheduler_secret)

    async for session in get_db():
        result = await session.execute(
            select(Prospect).where(Prospect.id == prospect_id)
        )
        prospect = result.scalar_one_or_none()
        if not prospect:
            raise HTTPException(status_code=404, detail=f"Prospect {prospect_id} not found")

        return {
            "id": prospect.id,
            "name": prospect.name,
            "email": prospect.email,
            "status": prospect.status.value if prospect.status else None,
            "claim_token": prospect.claim_token,
            "kliq_application_id": prospect.kliq_application_id,
            "kliq_store_url": prospect.kliq_store_url,
            "primary_platform": prospect.primary_platform.value if prospect.primary_platform else None,
            "niche_tags": prospect.niche_tags,
            "first_name": prospect.first_name,
        }


@router.get("/debug-linkedin")
async def debug_linkedin(x_scheduler_secret: str = Header(...)):
    """Debug LinkedIn data in prospects table."""
    _verify_secret(x_scheduler_secret)

    async for session in get_db():
        from sqlalchemy import text as t

        total = (await session.execute(t("SELECT COUNT(*) FROM prospects"))).scalar()
        with_url = (await session.execute(t("SELECT COUNT(*) FROM prospects WHERE linkedin_url IS NOT NULL"))).scalar()
        with_found = (await session.execute(t("SELECT COUNT(*) FROM prospects WHERE linkedin_found = TRUE"))).scalar()
        platforms = (await session.execute(t("SELECT primary_platform::text, COUNT(*) FROM prospects GROUP BY primary_platform"))).fetchall()
        sample = (await session.execute(t(
            "SELECT id, name, first_name, last_name, linkedin_url, linkedin_found, primary_platform::text "
            "FROM prospects WHERE primary_platform::text = 'WEBSITE' LIMIT 5"
        ))).fetchall()
        sample_all = (await session.execute(t(
            "SELECT id, name, first_name, last_name, linkedin_url, linkedin_found, primary_platform::text "
            "FROM prospects ORDER BY id DESC LIMIT 5"
        ))).fetchall()
        return {
            "total_prospects": total,
            "with_linkedin_url": with_url,
            "with_linkedin_found": with_found,
            "platforms": {str(r[0]): r[1] for r in platforms},
            "sample_website": [dict(r._mapping) for r in sample],
            "sample_recent": [dict(r._mapping) for r in sample_all],
        }


@router.post("/backfill-linkedin")
async def backfill_linkedin(x_scheduler_secret: str = Header(...)):
    """Backfill linkedin_url for ICF coaches using name-based LinkedIn search URLs."""
    _verify_secret(x_scheduler_secret)
    from urllib.parse import quote_plus

    async for session in get_db():
        result = await session.execute(text(
            "SELECT id, first_name, last_name FROM prospects "
            "WHERE linkedin_url IS NULL AND first_name IS NOT NULL AND last_name IS NOT NULL "
            "AND first_name != '' AND last_name != ''"
        ))
        rows = result.fetchall()
        updated = 0
        for row in rows:
            pid, first, last = row[0], row[1], row[2]
            url = f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(first + ' ' + last)}"
            await session.execute(
                text("UPDATE prospects SET linkedin_url = :url, linkedin_found = TRUE WHERE id = :id"),
                {"url": url, "id": pid},
            )
            updated += 1
        await session.commit()
        return {"backfilled": updated, "total_scanned": len(rows)}


@router.get("/iap-health")
async def iap_health_check(
    x_scheduler_secret: str = Header(...),
    cms_db: AsyncSession = Depends(get_cms_db),
):
    """IAP health check — queries CMS MySQL for subscription/receipt data."""
    _verify_secret(x_scheduler_secret)

    results = {}

    # 1. Apps with IAP enabled
    r = await cms_db.execute(text(
        "SELECT COUNT(*) as cnt FROM application_feature_setups WHERE enable_in_app_purchase = 1"
    ))
    results["iap_enabled_apps"] = r.scalar()

    # 2. Products with in_app_product_id set
    r = await cms_db.execute(text(
        "SELECT COUNT(*) as cnt FROM products WHERE in_app_product_id IS NOT NULL AND in_app_product_id != ''"
    ))
    results["products_with_iap_id"] = r.scalar()

    # 3. Sample products with IAP IDs
    r = await cms_db.execute(text(
        "SELECT p.id, p.application_id, p.name, p.in_app_product_id, p.unit_amount, p.interval, p.status_id "
        "FROM products p WHERE p.in_app_product_id IS NOT NULL AND p.in_app_product_id != '' "
        "ORDER BY p.created_at DESC LIMIT 20"
    ))
    results["sample_iap_products"] = [dict(row._mapping) for row in r.fetchall()]

    # 4. user_subscriptions table stats
    try:
        r = await cms_db.execute(text("SELECT COUNT(*) FROM user_subscriptions"))
        total_subs = r.scalar()
        r = await cms_db.execute(text(
            "SELECT status, COUNT(*) as cnt FROM user_subscriptions GROUP BY status"
        ))
        sub_statuses = {str(row[0]): row[1] for row in r.fetchall()}
        results["user_subscriptions"] = {"total": total_subs, "by_status": sub_statuses}
    except Exception as e:
        results["user_subscriptions"] = {"error": str(e)}

    # 5. application_subscriptions (subscription plans) — discover columns first
    try:
        r = await cms_db.execute(text("SELECT COUNT(*) FROM application_subscriptions"))
        total_app_subs = r.scalar()
        r = await cms_db.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'application_subscriptions'"
        ))
        app_sub_cols = [row[0] for row in r.fetchall()]
        r = await cms_db.execute(text(
            "SELECT * FROM application_subscriptions ORDER BY created_at DESC LIMIT 10"
        ))
        results["application_subscriptions"] = {
            "total": total_app_subs,
            "columns": app_sub_cols,
            "recent": [dict(row._mapping) for row in r.fetchall()],
        }
    except Exception as e:
        results["application_subscriptions"] = {"error": str(e)}

    # 6. app_store_revenues (Apple IAP receipts/revenue) — discover columns first
    try:
        r = await cms_db.execute(text("SELECT COUNT(*) FROM app_store_revenues"))
        total_revenues = r.scalar()
        r = await cms_db.execute(text(
            "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
            "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'app_store_revenues'"
        ))
        revenue_cols = [row[0] for row in r.fetchall()]
        r = await cms_db.execute(text(
            "SELECT * FROM app_store_revenues ORDER BY created_at DESC LIMIT 20"
        ))
        results["app_store_revenues"] = {
            "total": total_revenues,
            "columns": revenue_cols,
            "recent": [dict(row._mapping) for row in r.fetchall()],
        }
    except Exception as e:
        results["app_store_revenues"] = {"error": str(e)}

    # 7. user_subscription_invoices
    try:
        r = await cms_db.execute(text("SELECT COUNT(*) FROM user_subscription_invoices"))
        total_invoices = r.scalar()
        r = await cms_db.execute(text(
            "SELECT * FROM user_subscription_invoices ORDER BY created_at DESC LIMIT 10"
        ))
        results["user_subscription_invoices"] = {
            "total": total_invoices,
            "recent": [dict(row._mapping) for row in r.fetchall()],
        }
    except Exception as e:
        results["user_subscription_invoices"] = {"error": str(e)}

    # 8. Stripe-connected coaches (users with stripe_id)
    try:
        r = await cms_db.execute(text(
            "SELECT COUNT(*) FROM users WHERE stripe_id IS NOT NULL AND stripe_id != ''"
        ))
        results["users_with_stripe"] = r.scalar()
    except Exception as e:
        results["users_with_stripe"] = {"error": str(e)}

    return results
