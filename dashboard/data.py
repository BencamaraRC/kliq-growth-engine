"""Shared data access layer for the Streamlit dashboard.

Uses synchronous SQLAlchemy (Streamlit doesn't support async) to query
the Growth Engine PostgreSQL database. All functions return pandas
DataFrames or simple dicts for easy Streamlit rendering.
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, func, text

# Build sync DB URL from the async one
_async_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://bencamara@localhost:5433/kliq_growth_engine",
)
_sync_url = _async_url.replace("+asyncpg", "")
engine = create_engine(_sync_url, pool_pre_ping=True)


def get_kpi_summary() -> dict:
    """Top-level KPI metrics for the dashboard home."""
    with engine.connect() as conn:
        total = conn.execute(text("SELECT COUNT(*) FROM prospects")).scalar() or 0
        by_status = conn.execute(
            text("SELECT status, COUNT(*) as cnt FROM prospects GROUP BY status")
        ).fetchall()

        status_map = {row[0]: row[1] for row in by_status}

        stores = status_map.get("store_created", 0) + status_map.get("email_sent", 0) + status_map.get("claimed", 0)
        emails_sent = status_map.get("email_sent", 0) + status_map.get("claimed", 0)
        claimed = status_map.get("claimed", 0)

        total_emails = conn.execute(
            text("SELECT COUNT(*) FROM campaign_events WHERE email_status = 'sent'")
        ).scalar() or 0

        total_opened = conn.execute(
            text("SELECT COUNT(*) FROM campaign_events WHERE email_status = 'opened'")
        ).scalar() or 0

    return {
        "total_prospects": total,
        "discovered": status_map.get("discovered", 0),
        "scraped": status_map.get("scraped", 0),
        "content_generated": status_map.get("content_generated", 0),
        "stores_created": stores,
        "emails_sent": total_emails,
        "claimed": claimed,
        "rejected": status_map.get("rejected", 0),
        "open_rate": round(total_opened / total_emails * 100, 1) if total_emails else 0,
        "claim_rate": round(claimed / stores * 100, 1) if stores else 0,
    }


def get_funnel_data() -> pd.DataFrame:
    """Pipeline funnel: how many prospects at each stage."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT status, COUNT(*) as count
                FROM prospects
                GROUP BY status
                ORDER BY CASE status
                    WHEN 'discovered' THEN 1
                    WHEN 'scraped' THEN 2
                    WHEN 'content_generated' THEN 3
                    WHEN 'store_created' THEN 4
                    WHEN 'email_sent' THEN 5
                    WHEN 'claimed' THEN 6
                    WHEN 'rejected' THEN 7
                END
            """)
        ).fetchall()
    return pd.DataFrame(result, columns=["status", "count"])


def get_platform_breakdown() -> pd.DataFrame:
    """Prospects per platform."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT primary_platform, COUNT(*) as count
                FROM prospects
                GROUP BY primary_platform
                ORDER BY count DESC
            """)
        ).fetchall()
    return pd.DataFrame(result, columns=["platform", "count"])


def get_niche_distribution() -> pd.DataFrame:
    """Most common niche tags across all prospects."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT tag, COUNT(*) as count
                FROM prospects, jsonb_array_elements_text(niche_tags::jsonb) AS tag
                WHERE niche_tags IS NOT NULL
                GROUP BY tag
                ORDER BY count DESC
                LIMIT 20
            """)
        ).fetchall()
    return pd.DataFrame(result, columns=["niche", "count"])


def get_daily_activity(days: int = 30) -> pd.DataFrame:
    """Daily discovered/store_created/claimed counts."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT
                    DATE(discovered_at) as date,
                    COUNT(*) FILTER (WHERE status != 'rejected') as discovered,
                    COUNT(*) FILTER (WHERE store_created_at IS NOT NULL) as stores_created,
                    COUNT(*) FILTER (WHERE claimed_at IS NOT NULL) as claimed
                FROM prospects
                WHERE discovered_at >= :cutoff
                GROUP BY DATE(discovered_at)
                ORDER BY date
            """),
            {"cutoff": cutoff},
        ).fetchall()
    return pd.DataFrame(result, columns=["date", "discovered", "stores_created", "claimed"])


def get_prospects_table(
    status: str | None = None,
    platform: str | None = None,
    niche: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    """Paginated prospects list with filters."""
    conditions = []
    params: dict = {"limit": limit, "offset": offset}

    if status:
        conditions.append("status = :status")
        params["status"] = status
    if platform:
        conditions.append("primary_platform = :platform")
        params["platform"] = platform
    if niche:
        conditions.append("niche_tags::text ILIKE :niche")
        params["niche"] = f"%{niche}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    with engine.connect() as conn:
        result = conn.execute(
            text(f"""
                SELECT id, name, email, status, primary_platform,
                       follower_count, subscriber_count, niche_tags,
                       kliq_application_id, kliq_store_url, discovered_at, claimed_at
                FROM prospects
                {where}
                ORDER BY discovered_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).fetchall()

    return pd.DataFrame(
        result,
        columns=[
            "id", "name", "email", "status", "platform",
            "followers", "subscribers", "niches",
            "app_id", "store_url", "discovered", "claimed",
        ],
    )


def get_campaign_stats() -> dict:
    """Email campaign performance metrics."""
    with engine.connect() as conn:
        # Per-step stats
        step_stats = conn.execute(
            text("""
                SELECT
                    step,
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE email_status = 'sent') as sent,
                    COUNT(*) FILTER (WHERE email_status = 'opened') as opened,
                    COUNT(*) FILTER (WHERE email_status = 'clicked') as clicked,
                    COUNT(*) FILTER (WHERE email_status = 'bounced') as bounced,
                    COUNT(*) FILTER (WHERE email_status = 'unsubscribed') as unsubscribed
                FROM campaign_events
                GROUP BY step
                ORDER BY step
            """)
        ).fetchall()

    step_names = {1: "Store Ready", 2: "Reminder 1", 3: "Reminder 2", 4: "Claimed Confirmation"}
    steps = []
    for row in step_stats:
        step_num, total, sent, opened, clicked, bounced, unsub = row
        steps.append({
            "step": step_names.get(step_num, f"Step {step_num}"),
            "step_num": step_num,
            "total": total,
            "sent": sent,
            "opened": opened,
            "clicked": clicked,
            "bounced": bounced,
            "unsubscribed": unsub,
            "open_rate": round(opened / sent * 100, 1) if sent else 0,
            "click_rate": round(clicked / sent * 100, 1) if sent else 0,
        })

    return {"steps": steps}


def get_email_timeline(days: int = 30) -> pd.DataFrame:
    """Daily email sends grouped by step."""
    cutoff = datetime.utcnow() - timedelta(days=days)
    with engine.connect() as conn:
        result = conn.execute(
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
        ).fetchall()
    return pd.DataFrame(result, columns=["date", "step", "count"])


def get_recent_claims(limit: int = 20) -> pd.DataFrame:
    """Most recent store claims."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, name, email, primary_platform, kliq_application_id,
                       kliq_store_url, claimed_at
                FROM prospects
                WHERE status = 'claimed'
                ORDER BY claimed_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
    return pd.DataFrame(
        result,
        columns=["id", "name", "email", "platform", "app_id", "store_url", "claimed_at"],
    )


def get_prospect_detail(prospect_id: int) -> dict | None:
    """Full prospect detail for the intel page."""
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT * FROM prospects WHERE id = :id"),
            {"id": prospect_id},
        ).fetchone()

        if not row:
            return None

        prospect = dict(row._mapping)

        # Get platform profiles
        profiles = conn.execute(
            text("SELECT * FROM platform_profiles WHERE prospect_id = :id"),
            {"id": prospect_id},
        ).fetchall()
        prospect["platform_profiles"] = [dict(r._mapping) for r in profiles]

        # Get scraped content
        content = conn.execute(
            text("SELECT * FROM scraped_content WHERE prospect_id = :id ORDER BY view_count DESC"),
            {"id": prospect_id},
        ).fetchall()
        prospect["scraped_content"] = [dict(r._mapping) for r in content]

        # Get generated content
        generated = conn.execute(
            text("SELECT * FROM generated_content WHERE prospect_id = :id"),
            {"id": prospect_id},
        ).fetchall()
        prospect["generated_content"] = [dict(r._mapping) for r in generated]

        # Get campaign events
        events = conn.execute(
            text("SELECT * FROM campaign_events WHERE prospect_id = :id ORDER BY sent_at"),
            {"id": prospect_id},
        ).fetchall()
        prospect["campaign_events"] = [dict(r._mapping) for r in events]

    return prospect
