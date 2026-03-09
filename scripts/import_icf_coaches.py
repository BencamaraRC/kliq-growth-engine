"""Import ICF coaches from CSV into prospects table.

Usage:
    python scripts/import_icf_coaches.py <csv_path>

Parses the ICF coach directory CSV, extracts structured data,
and inserts each coach as a DISCOVERED prospect. Skips duplicates
by email.
"""

import asyncio
import csv
import json
import re
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# --- Name parsing ---

# Credential patterns to strip from name field
CREDENTIAL_PATTERNS = [
    r"\bACC\b",
    r"\bPCC\b",
    r"\bMCC\b",
    r"\bBCC\b",
    r"\bMBA\b",
    r"\bPhD\b",
    r"\bEdD\b",
    r"\bPsyD\b",
    r"\bJD\b",
    r"\bMD\b",
    r"\bRN\b",
    r"\bLPC\b",
    r"\bCPCC\b",
    r"\bCPC\b",
    r"\bCTPC\b",
    r"\bACTP\b",
    r"\bRev\.",
    r"\bDr\.",
    r"\bMr\.",
    r"\bMrs\.",
    r"\bMs\.",
    r"Certified Co Active Professional Coach",
    r"Certified Professional Co-Active Coach",
]


def parse_name(raw_name: str) -> tuple[str, str, str, list[str]]:
    """Parse raw ICF name field into (clean_name, first_name, last_name, credentials).

    Examples:
        "Darcy Denise (Wood) Dunker, ACC, PCC" -> ("Darcy Dunker", "Darcy", "Dunker", ["ACC", "PCC"])
        "Dr. Elaine Ann A Donoghue, ACC" -> ("Elaine Donoghue", "Elaine", "Donoghue", ["ACC"])
        "Mrs. Angela Marie Aaron, PCC, Certified Co Active Professional Coach"
            -> ("Angela Aaron", "Angela", "Aaron", ["PCC"])
    """
    # Extract credentials
    credentials = []
    for cred in ["ACC", "PCC", "MCC", "BCC", "MBA", "PhD", "EdD", "JD", "MD"]:
        if re.search(rf"\b{cred}\b", raw_name):
            credentials.append(cred)

    # Strip credentials and titles from name
    clean = raw_name
    for pat in CREDENTIAL_PATTERNS:
        clean = re.sub(pat, "", clean, flags=re.IGNORECASE)

    # Remove parenthetical nicknames/maiden names like (Wood)
    clean = re.sub(r"\([^)]*\)", "", clean)

    # Clean up commas, extra spaces
    clean = re.sub(r",", " ", clean)
    clean = re.sub(r"\s+", " ", clean).strip()

    parts = clean.split()
    if len(parts) >= 2:
        first_name = parts[0]
        last_name = parts[-1]
    elif len(parts) == 1:
        first_name = parts[0]
        last_name = ""
    else:
        first_name = raw_name.split(",")[0].strip()
        last_name = ""

    display_name = f"{first_name} {last_name}".strip()
    return display_name, first_name, last_name, credentials


def parse_location(loc: str) -> str:
    """Clean up location string."""
    if not loc:
        return ""
    # Already formatted as "City, ST UNITED STATES"
    return loc.strip()


def build_niche_tags(row: dict) -> list[str]:
    """Extract niche tags from coaching themes and other fields."""
    tags = []

    themes = row.get("Coaching Themes", "")
    if themes:
        tags.extend([t.strip() for t in themes.split("|") if t.strip()])

    # Add credential-based tags
    name = row.get("Name", "")
    if "PCC" in name or "MCC" in name:
        tags.append("ICF Certified Coach")
    if "ACC" in name:
        tags.append("ICF Associate Coach")

    return tags if tags else ["life coaching", "professional coaching"]


def extract_platform_id(profile_url: str) -> str:
    """Extract the coachcstkey GUID from the ICF profile URL."""
    match = re.search(r"coachcstkey=([A-F0-9-]+)", profile_url, re.IGNORECASE)
    return match.group(1) if match else ""


def build_linkedin_search_url(first_name: str, last_name: str) -> str:
    """Build a LinkedIn search URL from the coach's name.

    Since we don't have their exact profile URL, we link to a LinkedIn
    search that will typically surface them as the top result.
    """
    if not first_name or not last_name:
        return ""
    query = f"{first_name} {last_name}".strip()
    from urllib.parse import quote_plus
    return f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(query)}"


async def import_coaches(csv_path: str, db_url: str):
    """Read CSV and insert prospects."""
    engine = create_async_engine(db_url)
    session_factory = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # Read CSV
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Read {len(rows)} coaches from CSV")

    async with session_factory() as session:
        # Get existing emails to skip duplicates
        result = await session.execute(text("SELECT email FROM prospects WHERE email IS NOT NULL"))
        existing_emails = {r[0].lower() for r in result.fetchall()}
        print(f"Found {len(existing_emails)} existing prospects")

        inserted = 0
        skipped_dup = 0
        skipped_no_email = 0
        errors = 0

        for i, row in enumerate(rows):
            email = (row.get("Email") or "").strip()
            if not email:
                skipped_no_email += 1
                continue

            if email.lower() in existing_emails:
                skipped_dup += 1
                continue

            raw_name = (row.get("Name") or "").strip()
            if not raw_name:
                continue

            display_name, first_name, last_name, credentials = parse_name(raw_name)
            profile_url = (row.get("Profile_Link") or "").strip()
            platform_id = extract_platform_id(profile_url) or email.split("@")[0]
            website = (row.get("Website") or "").strip()
            if website == "Unspecified":
                website = ""
            location = parse_location(row.get("Location", ""))
            niche_tags = build_niche_tags(row)
            degrees = (row.get("Degrees") or "").strip()
            gender = (row.get("Gender") or "").strip()
            age = (row.get("Age") or "").strip()
            fee_range = (row.get("Fee Range") or "").strip()
            coaching_methods = (row.get("Coaching Methods") or "").strip()
            client_type = (row.get("Type of Client") or "").strip()

            # Build bio from available data
            bio_parts = []
            if credentials:
                bio_parts.append(f"ICF {', '.join(credentials)} Certified Coach.")
            if degrees:
                bio_parts.append(f"Education: {degrees}.")
            if location:
                bio_parts.append(f"Based in {location}.")
            if fee_range:
                bio_parts.append(f"Fee range: {fee_range}.")
            bio = " ".join(bio_parts) if bio_parts else ""

            # Store extra ICF data in social_links JSON
            extra_data = {}
            if credentials:
                extra_data["icf_credentials"] = credentials
            if degrees:
                extra_data["degrees"] = degrees
            if gender:
                extra_data["gender"] = gender
            if age:
                extra_data["age_range"] = age
            if fee_range:
                extra_data["fee_range"] = fee_range
            if coaching_methods:
                extra_data["coaching_methods"] = coaching_methods
            if client_type:
                extra_data["client_type"] = client_type
            if profile_url:
                extra_data["icf_profile_url"] = profile_url

            # Build LinkedIn search URL from name
            linkedin_url = build_linkedin_search_url(first_name, last_name)

            try:
                await session.execute(
                    text("""
                        INSERT INTO prospects (
                            name, first_name, last_name, email,
                            primary_platform, primary_platform_id, primary_platform_url,
                            website_url, location, niche_tags, bio,
                            social_links,
                            linkedin_url, linkedin_found,
                            follower_count, subscriber_count, content_count,
                            status
                        ) VALUES (
                            :name, :first, :last, :email,
                            CAST('WEBSITE' AS platform), :pid, :purl,
                            :website, :location, CAST(:niche AS jsonb), :bio,
                            CAST(:social AS json),
                            :linkedin_url, :linkedin_found,
                            0, 0, 0,
                            CAST('DISCOVERED' AS prospectstatus)
                        )
                    """),
                    {
                        "name": display_name,
                        "first": first_name,
                        "last": last_name,
                        "email": email,
                        "pid": platform_id,
                        "purl": profile_url,
                        "website": website or None,
                        "location": location or None,
                        "niche": json.dumps(niche_tags),
                        "bio": bio or None,
                        "social": json.dumps(extra_data) if extra_data else None,
                        "linkedin_url": linkedin_url or None,
                        "linkedin_found": bool(linkedin_url),
                    },
                )
                existing_emails.add(email.lower())
                inserted += 1

                if inserted % 100 == 0:
                    await session.commit()
                    print(f"  ... {inserted} inserted so far")

            except Exception as e:
                errors += 1
                if errors <= 5:
                    print(f"  Error on row {i + 1} ({display_name}): {e}")
                await session.rollback()

        # Final commit
        await session.commit()

    await engine.dispose()

    print("\nDone!")
    print(f"  Inserted:       {inserted}")
    print(f"  Skipped (dup):  {skipped_dup}")
    print(f"  Skipped (no email): {skipped_no_email}")
    print(f"  Errors:         {errors}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_icf_coaches.py <csv_path>")
        sys.exit(1)

    csv_path = sys.argv[1]
    if not Path(csv_path).exists():
        print(f"File not found: {csv_path}")
        sys.exit(1)

    # Use env var or default
    import os

    db_url = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@10.124.0.3:5432/kliq_growth_engine",
    )

    asyncio.run(import_coaches(csv_path, db_url))
