"""Backfill linkedin_url from social_links JSON for existing prospects.

Usage:
    python scripts/backfill_linkedin_urls.py

Scans all prospects where social_links contains a 'linkedin' key
and sets linkedin_url + linkedin_found = TRUE.
"""

import json
import os

from sqlalchemy import create_engine, text

# Build sync DB URL
_async_url = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://bencamara@localhost:5433/kliq_growth_engine",
)
_sync_url = _async_url.replace("+asyncpg", "")
engine = create_engine(_sync_url)


def backfill():
    with engine.begin() as conn:
        rows = conn.execute(
            text("""
                SELECT id, social_links
                FROM prospects
                WHERE social_links IS NOT NULL
                  AND linkedin_url IS NULL
            """)
        ).fetchall()

        updated = 0
        for row in rows:
            prospect_id = row[0]
            social_links = row[1]

            # Parse JSON if stored as string
            if isinstance(social_links, str):
                try:
                    social_links = json.loads(social_links)
                except (ValueError, TypeError):
                    continue

            if not isinstance(social_links, dict):
                continue

            linkedin = social_links.get("linkedin")
            if not linkedin:
                continue

            conn.execute(
                text("""
                    UPDATE prospects
                    SET linkedin_url = :url, linkedin_found = TRUE
                    WHERE id = :id
                """),
                {"url": linkedin, "id": prospect_id},
            )
            updated += 1

    print(f"Backfilled {updated} prospects with LinkedIn URLs")


if __name__ == "__main__":
    backfill()
