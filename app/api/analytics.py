"""Analytics API endpoints — ports sync queries from dashboard/data.py to async."""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db

router = APIRouter()


# --- Response Models ---


class KPISummary(BaseModel):
    total_prospects: int
    discovered: int
    scraped: int
    content_generated: int
    stores_created: int
    emails_sent: int
    claimed: int
    rejected: int
    open_rate: float
    claim_rate: float


class FunnelItem(BaseModel):
    status: str
    count: int


class PlatformItem(BaseModel):
    platform: str
    count: int


class NicheItem(BaseModel):
    niche: str
    count: int


class DailyActivityItem(BaseModel):
    date: str
    discovered: int
    stores_created: int
    claimed: int


class StatusCountItem(BaseModel):
    status: str
    count: int


class EmailStepStats(BaseModel):
    step: str
    step_num: int
    total: int
    sent: int
    opened: int
    clicked: int
    bounced: int
    unsubscribed: int
    open_rate: float
    click_rate: float


class EmailTimelineItem(BaseModel):
    date: str
    step: int
    count: int


class RecentClaimItem(BaseModel):
    id: int
    name: str
    email: str | None
    platform: str
    app_id: int | None
    store_url: str | None
    claimed_at: str | None


class RecentActivityItem(BaseModel):
    id: int
    name: str
    status: str
    platform: str
    updated_at: str | None


# --- Endpoints ---


@router.get("/kpi-summary", response_model=KPISummary)
async def kpi_summary(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    total = (await db.execute(text("SELECT COUNT(*) FROM prospects"))).scalar() or 0
    by_status = (
        await db.execute(text("SELECT status, COUNT(*) as cnt FROM prospects GROUP BY status"))
    ).fetchall()

    status_map = {row[0]: row[1] for row in by_status}

    stores = (
        status_map.get("STORE_CREATED", 0)
        + status_map.get("EMAIL_SENT", 0)
        + status_map.get("CLAIMED", 0)
    )
    claimed = status_map.get("CLAIMED", 0)

    total_emails = (
        await db.execute(
            text("SELECT COUNT(*) FROM campaign_events WHERE email_status = 'SENT'")
        )
    ).scalar() or 0

    total_opened = (
        await db.execute(
            text("SELECT COUNT(*) FROM campaign_events WHERE email_status = 'OPENED'")
        )
    ).scalar() or 0

    return KPISummary(
        total_prospects=total,
        discovered=status_map.get("DISCOVERED", 0),
        scraped=status_map.get("SCRAPED", 0),
        content_generated=status_map.get("CONTENT_GENERATED", 0),
        stores_created=stores,
        emails_sent=total_emails,
        claimed=claimed,
        rejected=status_map.get("REJECTED", 0),
        open_rate=round(total_opened / total_emails * 100, 1) if total_emails else 0,
        claim_rate=round(claimed / stores * 100, 1) if stores else 0,
    )


@router.get("/funnel", response_model=list[FunnelItem])
async def funnel(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = (
        await db.execute(
            text("""
                SELECT status, COUNT(*) as count
                FROM prospects
                GROUP BY status
                ORDER BY CASE status
                    WHEN 'DISCOVERED' THEN 1
                    WHEN 'SCRAPED' THEN 2
                    WHEN 'CONTENT_GENERATED' THEN 3
                    WHEN 'STORE_CREATED' THEN 4
                    WHEN 'EMAIL_SENT' THEN 5
                    WHEN 'CLAIMED' THEN 6
                    WHEN 'REJECTED' THEN 7
                END
            """)
        )
    ).fetchall()
    return [FunnelItem(status=row[0], count=row[1]) for row in result]


@router.get("/platforms", response_model=list[PlatformItem])
async def platforms(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = (
        await db.execute(
            text("""
                SELECT primary_platform, COUNT(*) as count
                FROM prospects
                GROUP BY primary_platform
                ORDER BY count DESC
            """)
        )
    ).fetchall()
    return [PlatformItem(platform=row[0], count=row[1]) for row in result]


@router.get("/niches", response_model=list[NicheItem])
async def niches(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = (
        await db.execute(
            text("""
                SELECT tag, COUNT(*) as count
                FROM prospects, jsonb_array_elements_text(niche_tags::jsonb) AS tag
                WHERE niche_tags IS NOT NULL
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 20
            """)
        )
    ).fetchall()
    return [NicheItem(niche=row[0], count=row[1]) for row in result]


@router.get("/daily-activity", response_model=list[DailyActivityItem])
async def daily_activity(
    days: int = Query(default=30, le=365),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = (
        await db.execute(
            text("""
                SELECT
                    DATE(discovered_at) as date,
                    COUNT(*) FILTER (WHERE status != 'REJECTED') as discovered,
                    COUNT(*) FILTER (WHERE store_created_at IS NOT NULL) as stores_created,
                    COUNT(*) FILTER (WHERE claimed_at IS NOT NULL) as claimed
                FROM prospects
                WHERE discovered_at >= :cutoff
                GROUP BY DATE(discovered_at)
                ORDER BY date
            """),
            {"cutoff": cutoff},
        )
    ).fetchall()
    return [
        DailyActivityItem(
            date=str(row[0]), discovered=row[1], stores_created=row[2], claimed=row[3]
        )
        for row in result
    ]


@router.get("/status-counts", response_model=list[StatusCountItem])
async def status_counts(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    rows = (
        await db.execute(
            text("SELECT status, COUNT(*) as cnt FROM prospects GROUP BY status")
        )
    ).fetchall()
    return [StatusCountItem(status=row[0], count=row[1]) for row in rows]


@router.get("/email-stats")
async def email_stats(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    step_stats = (
        await db.execute(
            text("""
                SELECT
                    step,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE email_status = 'SENT') as sent,
                    COUNT(*) FILTER (WHERE email_status = 'OPENED') as opened,
                    COUNT(*) FILTER (WHERE email_status = 'CLICKED') as clicked,
                    COUNT(*) FILTER (WHERE email_status = 'BOUNCED') as bounced,
                    COUNT(*) FILTER (WHERE email_status = 'UNSUBSCRIBED') as unsubscribed
                FROM campaign_events
                GROUP BY step
                ORDER BY step
            """)
        )
    ).fetchall()

    step_names = {1: "Store Ready", 2: "Reminder 1", 3: "Reminder 2", 4: "Claimed Confirmation"}
    steps = []
    for row in step_stats:
        step_num, total, sent, opened, clicked, bounced, unsub = row
        steps.append(
            EmailStepStats(
                step=step_names.get(step_num, f"Step {step_num}"),
                step_num=step_num,
                total=total,
                sent=sent,
                opened=opened,
                clicked=clicked,
                bounced=bounced,
                unsubscribed=unsub,
                open_rate=round(opened / sent * 100, 1) if sent else 0,
                click_rate=round(clicked / sent * 100, 1) if sent else 0,
            )
        )

    return {"steps": steps}


@router.get("/email-timeline", response_model=list[EmailTimelineItem])
async def email_timeline(
    days: int = Query(default=30, le=365),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    result = (
        await db.execute(
            text("""
                SELECT
                    DATE(sent_at) as date,
                    step,
                    COUNT(*) as count
                FROM campaign_events
                WHERE sent_at IS NOT NULL AND sent_at >= :cutoff
                GROUP BY DATE(sent_at), step
                ORDER BY date, step
            """),
            {"cutoff": cutoff},
        )
    ).fetchall()
    return [
        EmailTimelineItem(date=str(row[0]), step=row[1], count=row[2]) for row in result
    ]


@router.get("/recent-claims", response_model=list[RecentClaimItem])
async def recent_claims(
    limit: int = Query(default=20, le=100),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = (
        await db.execute(
            text("""
                SELECT id, name, email, primary_platform, kliq_application_id,
                       kliq_store_url, claimed_at
                FROM prospects
                WHERE status = 'CLAIMED'
                ORDER BY claimed_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
    ).fetchall()
    return [
        RecentClaimItem(
            id=row[0],
            name=row[1],
            email=row[2],
            platform=row[3],
            app_id=row[4],
            store_url=row[5],
            claimed_at=str(row[6]) if row[6] else None,
        )
        for row in result
    ]


@router.get("/recent-activity", response_model=list[RecentActivityItem])
async def recent_activity(
    limit: int = Query(default=10, le=50),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    result = (
        await db.execute(
            text("""
                SELECT id, name, status, primary_platform, updated_at
                FROM prospects
                ORDER BY updated_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        )
    ).fetchall()
    return [
        RecentActivityItem(
            id=row[0],
            name=row[1],
            status=row[2],
            platform=row[3],
            updated_at=str(row[4]) if row[4] else None,
        )
        for row in result
    ]
