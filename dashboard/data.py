"""Shared data access layer for the Streamlit dashboard.

Uses synchronous SQLAlchemy (Streamlit doesn't support async) to query
the Growth Engine PostgreSQL database. All functions return pandas
DataFrames or simple dicts for easy Streamlit rendering.
"""

import os
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import create_engine, text

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

        stores = (
            status_map.get("STORE_CREATED", 0)
            + status_map.get("EMAIL_SENT", 0)
            + status_map.get("CLAIMED", 0)
        )
        _emails_sent = status_map.get("EMAIL_SENT", 0) + status_map.get("CLAIMED", 0)
        claimed = status_map.get("CLAIMED", 0)

        total_emails = (
            conn.execute(
                text("SELECT COUNT(*) FROM campaign_events WHERE email_status = 'SENT'")
            ).scalar()
            or 0
        )

        total_opened = (
            conn.execute(
                text("SELECT COUNT(*) FROM campaign_events WHERE email_status = 'OPENED'")
            ).scalar()
            or 0
        )

    return {
        "total_prospects": total,
        "discovered": status_map.get("DISCOVERED", 0),
        "scraped": status_map.get("SCRAPED", 0),
        "content_generated": status_map.get("CONTENT_GENERATED", 0),
        "stores_created": stores,
        "emails_sent": total_emails,
        "claimed": claimed,
        "rejected": status_map.get("REJECTED", 0),
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
                    WHEN 'DISCOVERED' THEN 1
                    WHEN 'SCRAPED' THEN 2
                    WHEN 'CONTENT_GENERATED' THEN 3
                    WHEN 'STORE_CREATED' THEN 4
                    WHEN 'EMAIL_SENT' THEN 5
                    WHEN 'CLAIMED' THEN 6
                    WHEN 'REJECTED' THEN 7
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
                    COUNT(*) FILTER (WHERE status != 'REJECTED') as discovered,
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


def _build_prospect_filters(
    status: str | None = None,
    platform: str | None = None,
    niche: str | None = None,
    search: str | None = None,
) -> tuple[str, dict]:
    """Build WHERE clause and params for prospect queries."""
    conditions = []
    params: dict = {}
    if status:
        conditions.append("status = :status")
        params["status"] = status
    if platform:
        conditions.append("primary_platform = :platform")
        params["platform"] = platform
    if niche:
        conditions.append("niche_tags::text ILIKE :niche")
        params["niche"] = f"%{niche}%"
    if search:
        conditions.append("(name ILIKE :search OR email ILIKE :search)")
        params["search"] = f"%{search}%"
    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where, params


def get_prospects_table(
    status: str | None = None,
    platform: str | None = None,
    niche: str | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> pd.DataFrame:
    """Paginated prospects list with filters."""
    where, params = _build_prospect_filters(status, platform, niche, search)
    params["limit"] = limit
    params["offset"] = offset

    with engine.connect() as conn:
        result = conn.execute(
            text(f"""
                SELECT id, name, profile_image_url, email, status, primary_platform,
                       primary_platform_url, website_url, social_links,
                       follower_count, subscriber_count,
                       niche_tags, kliq_application_id, kliq_store_url,
                       discovered_at, claimed_at
                FROM prospects
                {where}
                ORDER BY discovered_at DESC
                LIMIT :limit OFFSET :offset
            """),
            params,
        ).fetchall()

    df = pd.DataFrame(
        result,
        columns=[
            "id",
            "name",
            "avatar",
            "email",
            "status",
            "platform",
            "platform_url",
            "website",
            "social_links_raw",
            "followers",
            "subscribers",
            "niches",
            "app_id",
            "store_url",
            "discovered",
            "claimed",
        ],
    )

    # Extract individual social link URLs from JSON
    import json as _json

    def _parse_social(raw, key):
        if raw is None:
            return None
        if isinstance(raw, str):
            try:
                raw = _json.loads(raw)
            except (ValueError, TypeError):
                return None
        if isinstance(raw, dict):
            return raw.get(key)
        return None

    df["instagram"] = df["social_links_raw"].apply(lambda r: _parse_social(r, "instagram"))
    df["youtube"] = df["social_links_raw"].apply(lambda r: _parse_social(r, "youtube"))
    df["tiktok"] = df["social_links_raw"].apply(lambda r: _parse_social(r, "tiktok"))
    df["twitter"] = df["social_links_raw"].apply(lambda r: _parse_social(r, "twitter"))
    df.drop(columns=["social_links_raw"], inplace=True)

    # Store preview link (full URL for LinkColumn)
    df["store_preview"] = df["id"].apply(
        lambda pid: f"http://localhost:8501/store_preview?id={pid}"
    )

    return df


def get_prospects_count(
    status: str | None = None,
    platform: str | None = None,
    niche: str | None = None,
    search: str | None = None,
) -> int:
    """Count prospects matching filters (for pagination)."""
    where, params = _build_prospect_filters(status, platform, niche, search)
    with engine.connect() as conn:
        return conn.execute(text(f"SELECT COUNT(*) FROM prospects {where}"), params).scalar() or 0


def get_all_platforms() -> list[str]:
    """Get all distinct platforms for filter dropdowns."""
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT DISTINCT primary_platform FROM prospects ORDER BY primary_platform")
        ).fetchall()
    return [row[0] for row in result if row[0]]


def get_all_niches() -> list[str]:
    """Get all distinct niche tags for filter dropdowns."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT DISTINCT tag
                FROM prospects, jsonb_array_elements_text(niche_tags::jsonb) AS tag
                WHERE niche_tags IS NOT NULL
                ORDER BY tag
            """)
        ).fetchall()
    return [row[0] for row in result]


def get_campaign_stats() -> dict:
    """Email campaign performance metrics."""
    with engine.connect() as conn:
        # Per-step stats
        step_stats = conn.execute(
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
        ).fetchall()

    step_names = {1: "Store Ready", 2: "Reminder 1", 3: "Reminder 2", 4: "Claimed Confirmation"}
    steps = []
    for row in step_stats:
        step_num, total, sent, opened, clicked, bounced, unsub = row
        steps.append(
            {
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
            }
        )

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
                WHERE status = 'CLAIMED'
                ORDER BY claimed_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
    return pd.DataFrame(
        result,
        columns=["id", "name", "email", "platform", "app_id", "store_url", "claimed_at"],
    )


def get_prospects_for_operations(
    status: str | None = None,
    platform: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Prospects list for the operations page, includes claim_token for preview URLs."""
    where, params = _build_prospect_filters(status=status, platform=platform, search=search)
    params["limit"] = limit

    with engine.connect() as conn:
        result = conn.execute(
            text(f"""
                SELECT id, name, email, status, primary_platform,
                       follower_count, claim_token, kliq_store_url, discovered_at
                FROM prospects
                {where}
                ORDER BY discovered_at DESC
                LIMIT :limit
            """),
            params,
        ).fetchall()

    return pd.DataFrame(
        result,
        columns=[
            "id", "name", "email", "status", "platform",
            "followers", "claim_token", "store_url", "discovered",
        ],
    )


def get_status_counts() -> dict[str, int]:
    """Count of prospects per status (for batch operation buttons)."""
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT status, COUNT(*) as cnt FROM prospects GROUP BY status")
        ).fetchall()
    return {row[0]: row[1] for row in rows}


def get_recent_task_prospects(limit: int = 10) -> pd.DataFrame:
    """Most recently updated prospects for the activity feed."""
    with engine.connect() as conn:
        result = conn.execute(
            text("""
                SELECT id, name, status, primary_platform, updated_at
                FROM prospects
                ORDER BY updated_at DESC
                LIMIT :limit
            """),
            {"limit": limit},
        ).fetchall()
    return pd.DataFrame(
        result,
        columns=["id", "name", "status", "platform", "updated_at"],
    )


def get_linkedin_queue(
    status: str | None = None,
    search: str | None = None,
    limit: int = 100,
) -> pd.DataFrame:
    """Prospects with LinkedIn URLs and their outreach status."""
    conditions = ["p.linkedin_found = TRUE"]
    params: dict = {"limit": limit}

    if status:
        if status.upper() == "QUEUED":
            conditions.append("lo.id IS NULL")
        else:
            conditions.append("lo.status = :status")
            params["status"] = status.upper()
    if search:
        conditions.append("(p.name ILIKE :search OR p.email ILIKE :search)")
        params["search"] = f"%{search}%"

    where = "WHERE " + " AND ".join(conditions)

    with engine.connect() as conn:
        result = conn.execute(
            text(f"""
                SELECT
                    p.id, p.name, p.email, p.niche_tags, p.linkedin_url,
                    p.follower_count,
                    COALESCE(lo.status, 'QUEUED') as outreach_status,
                    lo.connection_note, lo.sent_at, lo.accepted_at
                FROM prospects p
                LEFT JOIN linkedin_outreach lo ON lo.prospect_id = p.id
                {where}
                ORDER BY p.discovered_at DESC
                LIMIT :limit
            """),
            params,
        ).fetchall()

    return pd.DataFrame(
        result,
        columns=[
            "id", "name", "email", "niches", "linkedin_url",
            "followers", "outreach_status", "connection_note",
            "sent_at", "accepted_at",
        ],
    )


def get_linkedin_stats() -> dict:
    """LinkedIn outreach aggregate statistics."""
    with engine.connect() as conn:
        total = conn.execute(
            text("SELECT COUNT(*) FROM prospects WHERE linkedin_found = TRUE")
        ).scalar() or 0

        status_rows = conn.execute(
            text("SELECT status, COUNT(*) FROM linkedin_outreach GROUP BY status")
        ).fetchall()

    status_counts = {row[0]: row[1] for row in status_rows}
    outreach_total = sum(status_counts.values())

    sent = (
        status_counts.get("SENT", 0)
        + status_counts.get("ACCEPTED", 0)
        + status_counts.get("DECLINED", 0)
        + status_counts.get("NO_RESPONSE", 0)
    )
    accepted = status_counts.get("ACCEPTED", 0)

    return {
        "total_with_linkedin": total,
        "queued": total - outreach_total,
        "copied": status_counts.get("COPIED", 0),
        "sent": status_counts.get("SENT", 0),
        "accepted": accepted,
        "declined": status_counts.get("DECLINED", 0),
        "no_response": status_counts.get("NO_RESPONSE", 0),
        "accept_rate": round(accepted / sent * 100, 1) if sent > 0 else 0.0,
    }


def get_linkedin_outreach_detail(prospect_id: int) -> dict | None:
    """Single prospect LinkedIn outreach record."""
    with engine.connect() as conn:
        row = conn.execute(
            text("""
                SELECT lo.*, p.name, p.email, p.linkedin_url, p.niche_tags
                FROM linkedin_outreach lo
                JOIN prospects p ON p.id = lo.prospect_id
                WHERE lo.prospect_id = :id
            """),
            {"id": prospect_id},
        ).fetchone()

    if not row:
        return None
    return dict(row._mapping)


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

        # Get scraped pricing
        pricing = conn.execute(
            text("SELECT * FROM scraped_pricing WHERE prospect_id = :id ORDER BY price_amount"),
            {"id": prospect_id},
        ).fetchall()
        prospect["scraped_pricing"] = [dict(r._mapping) for r in pricing]

    return prospect
