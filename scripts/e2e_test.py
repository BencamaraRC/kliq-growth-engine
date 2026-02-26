#!/usr/bin/env python3
"""End-to-end pipeline test for the KLIQ Growth Engine.

Usage:
    python scripts/e2e_test.py @sydneycummings
    python scripts/e2e_test.py https://www.youtube.com/@JeffNippard
    python scripts/e2e_test.py --channel-id UCxxxxxxx

Options:
    --max-videos N   Max videos to scrape (default: 5)
    --max-blogs N    Max blogs to generate (default: 3)
    --skip-ai        Skip AI generation (test scraping only)
    --skip-db        Skip database storage (print results only)

Prerequisites:
    - PostgreSQL running on port 5433 (database: kliq_growth_engine)
    - ANTHROPIC_API_KEY set in .env or environment
    - yt-dlp installed
    - Migrations applied (alembic upgrade head)
"""

import argparse
import asyncio
import json
import os
import re
import subprocess
import sys
import time

# Add project root to path so we can import app modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Load .env before importing app modules
from dotenv import load_dotenv
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

import psycopg2
import psycopg2.extras


# ─── Step 0: Prerequisites ────────────────────────────────────────────────────


def check_prerequisites(skip_db: bool = False, skip_ai: bool = False) -> dict:
    """Verify all dependencies before starting the pipeline."""
    print("\n[Step 0] Checking prerequisites...")
    results = {}

    # yt-dlp
    try:
        out = subprocess.run(
            ["yt-dlp", "--version"], capture_output=True, text=True, timeout=10
        )
        results["yt-dlp"] = out.stdout.strip()
        print(f"  ✓ yt-dlp {results['yt-dlp']}")
    except Exception as e:
        print(f"  ✗ yt-dlp not found: {e}")
        sys.exit(1)

    # youtube-transcript-api
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        results["transcripts"] = True
        print("  ✓ youtube-transcript-api")
    except ImportError:
        print("  ✗ youtube-transcript-api not installed (pip install youtube-transcript-api)")
        results["transcripts"] = False

    # PostgreSQL
    if not skip_db:
        try:
            conn = psycopg2.connect(
                host="localhost", port=5433,
                dbname="kliq_growth_engine", user="bencamara",
            )
            conn.close()
            results["db"] = True
            print("  ✓ PostgreSQL (port 5433)")
        except Exception as e:
            print(f"  ✗ PostgreSQL: {e}")
            sys.exit(1)
    else:
        print("  - PostgreSQL (skipped)")

    # Anthropic API key
    if not skip_ai:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key:
            results["api_key"] = True
            print(f"  ✓ ANTHROPIC_API_KEY ({api_key[:12]}...)")
        else:
            print("  ✗ ANTHROPIC_API_KEY not set")
            print("\n  To fix:")
            print("  1. Go to https://console.anthropic.com/settings/keys")
            print("  2. Create a new API key")
            print("  3. Add to .env: ANTHROPIC_API_KEY=sk-ant-api03-...")
            sys.exit(1)
    else:
        print("  - ANTHROPIC_API_KEY (skipped)")

    print()
    return results


# ─── Step 1: YouTube Scraping via yt-dlp ──────────────────────────────────────


def resolve_channel_url(channel_input: str) -> str:
    """Normalize various YouTube channel input formats to a URL."""
    channel_input = channel_input.strip()

    if channel_input.startswith("http"):
        return channel_input

    if channel_input.startswith("@"):
        return f"https://www.youtube.com/{channel_input}"

    if channel_input.startswith("UC"):
        return f"https://www.youtube.com/channel/{channel_input}"

    # Assume it's a handle without @
    return f"https://www.youtube.com/@{channel_input}"


def scrape_youtube_channel(channel_input: str, max_videos: int = 5) -> tuple:
    """Scrape a YouTube channel using yt-dlp (no API key needed).

    Returns:
        (profile_dict, list_of_content_dicts)
    """
    channel_url = resolve_channel_url(channel_input)
    print(f"[Step 1] Scraping YouTube channel: {channel_url}")

    # 1a. Get video list from channel
    print(f"  Fetching up to {max_videos} videos...")
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--dump-json",
        "--playlist-items", f"1:{max_videos * 2}",  # fetch extra in case some fail
        f"{channel_url}/videos",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    if result.returncode != 0:
        print(f"  Error: {result.stderr[:200]}")
        sys.exit(1)

    video_entries = []
    for line in result.stdout.strip().split("\n"):
        if line.strip():
            try:
                video_entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    if not video_entries:
        print("  No videos found!")
        sys.exit(1)

    # Extract channel info from first entry (flat-playlist uses playlist_* fields)
    first = video_entries[0]
    channel_name = (
        first.get("playlist_channel")
        or first.get("playlist_uploader")
        or first.get("channel")
        or first.get("uploader")
        or "Unknown"
    )
    channel_id = (
        first.get("playlist_channel_id")
        or first.get("playlist_id")
        or first.get("channel_id")
        or first.get("uploader_id")
        or ""
    )
    channel_url_canonical = first.get("channel_url", first.get("uploader_url", channel_url))

    print(f"  Channel: {channel_name} (ID: {channel_id})")
    print(f"  Videos found: {len(video_entries)}")

    # 1b. Get full details for top videos
    videos = []
    for i, entry in enumerate(video_entries[:max_videos]):
        video_id = entry.get("id", entry.get("url", ""))
        if not video_id:
            continue

        print(f"  [{i+1}/{min(max_videos, len(video_entries))}] Fetching: {entry.get('title', video_id)[:60]}...")

        # Full video metadata
        vid_cmd = [
            "yt-dlp", "--dump-json", "--skip-download",
            f"https://www.youtube.com/watch?v={video_id}",
        ]
        vid_result = subprocess.run(vid_cmd, capture_output=True, text=True, timeout=60)

        if vid_result.returncode != 0:
            print(f"    Skipped (error)")
            continue

        try:
            vid_data = json.loads(vid_result.stdout)
        except json.JSONDecodeError:
            continue

        # Get transcript (v1.2+ API: instantiate then .fetch())
        transcript = ""
        try:
            from youtube_transcript_api import YouTubeTranscriptApi
            api = YouTubeTranscriptApi()
            result_t = api.fetch(video_id)
            transcript = " ".join(s.text for s in result_t.snippets)
            print(f"    Transcript: {len(transcript)} chars")
        except Exception:
            print(f"    Transcript: not available")

        thumbnail = vid_data.get("thumbnail", "")
        if not thumbnail:
            thumbs = vid_data.get("thumbnails", [])
            if thumbs:
                thumbnail = thumbs[-1].get("url", "")

        videos.append({
            "video_id": video_id,
            "title": vid_data.get("title", ""),
            "description": vid_data.get("description", ""),
            "transcript": transcript,
            "thumbnail_url": thumbnail,
            "view_count": vid_data.get("view_count", 0),
            "like_count": vid_data.get("like_count", 0),
            "upload_date": vid_data.get("upload_date", ""),
            "duration": vid_data.get("duration", 0),
            "tags": vid_data.get("tags", []),
        })

        # Rate limit
        if i < len(video_entries) - 1:
            time.sleep(2)

    # 1c. Build profile dict
    # Get subscriber count and description from full video metadata
    description = ""
    subscriber_count = 0
    profile_image_url = ""
    banner_image_url = ""

    # Extract channel-level info from the full video data we already fetched
    if videos:
        first_vid_cmd = [
            "yt-dlp", "--dump-json", "--skip-download",
            f"https://www.youtube.com/watch?v={videos[0]['video_id']}",
        ]
        first_vid_result = subprocess.run(first_vid_cmd, capture_output=True, text=True, timeout=30)
        if first_vid_result.returncode == 0:
            try:
                ch_data = json.loads(first_vid_result.stdout)
                subscriber_count = ch_data.get("channel_follower_count", 0) or 0
                description = ch_data.get("channel_description") or ch_data.get("description", "")
                # Get channel avatar from thumbnails
                for thumb in ch_data.get("thumbnails", []):
                    url = thumb.get("url", "")
                    if "yt3.ggpht" in url or "yt3.googleusercontent" in url:
                        profile_image_url = url
                        break
            except json.JSONDecodeError:
                pass

    # Fallback description from video entries
    if not description:
        for v in video_entries:
            if v.get("description"):
                description = v.get("description", "")
                break

    # Extract email from description/bio
    email = None
    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", description)
    if email_match:
        email = email_match.group()

    # Extract niche tags from description
    niche_tags = _extract_niche_tags(description)

    profile = {
        "platform": "youtube",
        "platform_id": channel_id,
        "name": channel_name,
        "bio": description,
        "email": email,
        "profile_image_url": profile_image_url,
        "banner_image_url": banner_image_url,
        "website_url": "",
        "social_links": {},
        "niche_tags": niche_tags,
        "follower_count": subscriber_count,
        "subscriber_count": subscriber_count,
        "content_count": len(videos),
    }

    print(f"\n  Profile: {channel_name}")
    print(f"  Subscribers: {subscriber_count:,}")
    print(f"  Email: {email or 'not found'}")
    print(f"  Niches: {', '.join(niche_tags) or 'none detected'}")
    print(f"  Videos scraped: {len(videos)}")
    transcripts_count = sum(1 for v in videos if v["transcript"])
    print(f"  Transcripts: {transcripts_count}/{len(videos)}")
    print()

    return profile, videos


def _extract_niche_tags(text: str) -> list[str]:
    """Extract fitness/wellness niche tags from text."""
    if not text:
        return []

    niche_keywords = {
        "fitness": "fitness",
        "workout": "fitness",
        "exercise": "fitness",
        "bodybuilding": "bodybuilding",
        "powerlifting": "powerlifting",
        "crossfit": "crossfit",
        "yoga": "yoga",
        "pilates": "pilates",
        "nutrition": "nutrition",
        "diet": "nutrition",
        "weight loss": "weight loss",
        "strength training": "strength training",
        "personal trainer": "personal training",
        "coaching": "coaching",
        "wellness": "wellness",
        "mental health": "mental health",
        "meditation": "meditation",
        "hiit": "HIIT",
        "calisthenics": "calisthenics",
        "running": "running",
        "cycling": "cycling",
        "swimming": "swimming",
        "martial arts": "martial arts",
        "boxing": "boxing",
        "mma": "MMA",
    }

    text_lower = text.lower()
    found = set()
    for keyword, tag in niche_keywords.items():
        if keyword in text_lower:
            found.add(tag)

    return sorted(found)


# ─── Step 2: Store to PostgreSQL ──────────────────────────────────────────────


def get_db_connection():
    return psycopg2.connect(
        host="localhost", port=5433,
        dbname="kliq_growth_engine", user="bencamara",
    )


def store_prospect(conn, profile: dict) -> int:
    """Insert or update prospect in PostgreSQL. Returns prospect_id."""
    print("[Step 2] Storing prospect in PostgreSQL...")

    with conn.cursor() as cur:
        # Check if prospect exists by platform_id
        cur.execute(
            "SELECT id FROM prospects WHERE primary_platform_id = %s",
            (profile["platform_id"],),
        )
        existing = cur.fetchone()

        if existing:
            prospect_id = existing[0]
            cur.execute("""
                UPDATE prospects SET
                    status = 'SCRAPED', name = %s, email = %s, bio = %s,
                    profile_image_url = %s, banner_image_url = %s,
                    website_url = %s, social_links = %s, niche_tags = %s,
                    follower_count = %s, subscriber_count = %s, content_count = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                profile["name"], profile["email"], profile["bio"],
                profile["profile_image_url"], profile["banner_image_url"],
                profile["website_url"], json.dumps(profile["social_links"]),
                json.dumps(profile["niche_tags"]),
                profile["follower_count"], profile["subscriber_count"],
                profile["content_count"], prospect_id,
            ))
            print(f"  Updated existing prospect ID={prospect_id}")
        else:
            cur.execute("""
                INSERT INTO prospects (
                    status, name, email, primary_platform, primary_platform_id,
                    primary_platform_url, bio, profile_image_url, banner_image_url,
                    website_url, social_links, niche_tags,
                    follower_count, subscriber_count, content_count
                ) VALUES (
                    'SCRAPED', %s, %s, 'YOUTUBE', %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                profile["name"], profile["email"],
                profile["platform_id"],
                f"https://www.youtube.com/channel/{profile['platform_id']}",
                profile["bio"],
                profile["profile_image_url"], profile["banner_image_url"],
                profile["website_url"],
                json.dumps(profile["social_links"]),
                json.dumps(profile["niche_tags"]),
                profile["follower_count"], profile["subscriber_count"],
                profile["content_count"],
            ))
            prospect_id = cur.fetchone()[0]
            print(f"  Created prospect ID={prospect_id}")

    conn.commit()
    return prospect_id


def store_scraped_content(conn, prospect_id: int, videos: list[dict]):
    """Store scraped videos in PostgreSQL."""
    print(f"  Storing {len(videos)} videos...")

    with conn.cursor() as cur:
        # Clear existing scraped content for this prospect
        cur.execute(
            "DELETE FROM scraped_content WHERE prospect_id = %s",
            (prospect_id,),
        )

        for video in videos:
            cur.execute("""
                INSERT INTO scraped_content (
                    prospect_id, platform, content_type, title, description,
                    body, url, thumbnail_url, view_count, engagement_count,
                    tags
                ) VALUES (
                    %s, 'YOUTUBE', 'video', %s, %s, %s, %s, %s, %s, %s, %s
                )
            """, (
                prospect_id,
                video["title"],
                video["description"],
                video["transcript"],
                f"https://www.youtube.com/watch?v={video['video_id']}",
                video["thumbnail_url"],
                video["view_count"],
                video.get("like_count", 0),
                json.dumps(video.get("tags", [])),
            ))

    conn.commit()
    print(f"  Stored {len(videos)} videos")
    print()


# ─── Step 3-4: AI Content Generation + Storage ───────────────────────────────


def run_ai_generation(profile: dict, videos: list[dict]) -> dict:
    """Run all AI generators and return results."""
    from app.ai.client import AIClient
    from app.ai.bio_generator import generate_bio
    from app.ai.blog_generator import generate_blogs_batch
    from app.ai.pricing_analyzer import analyze_pricing
    from app.ai.seo_generator import generate_seo
    from app.scrapers.color_extractor import extract_colors_from_url

    client = AIClient()
    results = {}

    # 3a. Bio
    print("[Step 3] AI Content Generation")
    print("  [3a] Generating coach bio...")
    content_titles = [v["title"] for v in videos if v["title"]]

    bio = asyncio.run(generate_bio(
        client=client,
        name=profile["name"],
        platform="youtube",
        bio=profile["bio"],
        niche_tags=profile["niche_tags"],
        follower_count=profile["follower_count"],
        content_count=len(videos),
        content_titles=content_titles,
    ))
    results["bio"] = bio
    print(f"       Tagline: {bio.tagline}")
    print(f"       Specialties: {', '.join(bio.specialties)}")

    # 3b. Blogs
    print("  [3b] Generating blog posts from transcripts...")
    video_dicts = []
    for v in videos:
        # Use transcript if available, fall back to description
        text = v["transcript"] or v["description"]
        if text and len(text) >= 200:
            video_dicts.append({
                "title": v["title"],
                "transcript": text,
                "description": v["description"],
                "view_count": v["view_count"],
                "url": f"https://www.youtube.com/watch?v={v['video_id']}",
            })
    blogs = asyncio.run(generate_blogs_batch(
        client=client,
        coach_name=profile["name"],
        videos=video_dicts,
        max_blogs=3,
    ))
    results["blogs"] = blogs
    for b in blogs:
        print(f"       - {b.blog_title}")

    # 3c. Pricing
    print("  [3c] Analyzing pricing...")
    pricing = asyncio.run(analyze_pricing(
        client=client,
        name=profile["name"],
        niche_tags=profile["niche_tags"],
        follower_count=profile["follower_count"],
        pricing_tiers=[],  # YouTube has no native pricing
        content_types=["videos", "blog posts"],
    ))
    results["pricing"] = pricing
    for p in pricing.products:
        sym = "$" if p.currency == "USD" else "£"
        interval = f"/{p.interval}" if p.interval else ""
        rec = " [RECOMMENDED]" if p.recommended else ""
        print(f"       - {p.name}: {sym}{p.price_cents/100:.2f}{interval}{rec}")

    # 3d. SEO
    print("  [3d] Generating SEO metadata...")
    seo = asyncio.run(generate_seo(
        client=client,
        name=profile["name"],
        tagline=bio.tagline,
        specialties=bio.specialties,
        niche_tags=profile["niche_tags"],
        content_titles=content_titles[:10],
    ))
    results["seo"] = seo
    print(f"       Slug: {seo.store_slug}")
    print(f"       Title: {seo.seo_title}")

    # 3e. Colors
    print("  [3e] Extracting brand colors...")
    if profile["profile_image_url"]:
        colors = asyncio.run(extract_colors_from_url(profile["profile_image_url"]))
    else:
        # Try to extract from a video thumbnail
        thumb_url = next((v["thumbnail_url"] for v in videos if v["thumbnail_url"]), "")
        colors = asyncio.run(extract_colors_from_url(thumb_url)) if thumb_url else None

    results["colors"] = colors
    if colors:
        print(f"       Primary: {colors.primary}")
        print(f"       Secondary: {colors.secondary}")
        print(f"       Accent: {colors.accent}")
    else:
        print("       Using default colors")

    results["token_usage"] = client.usage_summary
    print(f"\n  Token usage: {client.usage_summary}")
    print()

    return results


def store_generated_content(conn, prospect_id: int, results: dict, videos: list[dict]):
    """Store AI-generated content in PostgreSQL."""
    print("[Step 4] Storing generated content...")

    with conn.cursor() as cur:
        # Clear existing generated content for this prospect
        cur.execute(
            "DELETE FROM generated_content WHERE prospect_id = %s",
            (prospect_id,),
        )

        # Bio
        bio = results["bio"]
        cur.execute("""
            INSERT INTO generated_content (prospect_id, content_type, title, body)
            VALUES (%s, 'bio', %s, %s)
        """, (prospect_id, bio.tagline, json.dumps({
            "tagline": bio.tagline,
            "short_bio": bio.short_bio,
            "long_bio": bio.long_bio,
            "specialties": bio.specialties,
            "coaching_style": bio.coaching_style,
            "store_name": results.get("seo", None) and results["seo"].store_slug.replace("-", " ").title() or "",
        })))

        # Blogs
        for blog in results["blogs"]:
            # Find matching video for thumbnail
            thumbnail = ""
            for v in videos:
                if v["title"] and v["title"] in blog.source_video_url:
                    thumbnail = v["thumbnail_url"]
                    break
            # Fallback: match by video ID in source URL
            if not thumbnail and blog.source_video_url:
                vid_id = blog.source_video_url.split("v=")[-1] if "v=" in blog.source_video_url else ""
                for v in videos:
                    if v["video_id"] == vid_id:
                        thumbnail = v["thumbnail_url"]
                        break

            cur.execute("""
                INSERT INTO generated_content (prospect_id, content_type, title, body)
                VALUES (%s, 'blog', %s, %s)
            """, (prospect_id, blog.blog_title, json.dumps({
                "excerpt": blog.excerpt,
                "body_html": blog.body_html,
                "tags": blog.tags,
                "seo_title": blog.seo_title,
                "seo_description": blog.seo_description,
                "source_video_url": blog.source_video_url,
                "thumbnail": thumbnail,
                "views": 0,
            })))

        # Products
        for product in results["pricing"].products:
            cur.execute("""
                INSERT INTO generated_content (prospect_id, content_type, title, body)
                VALUES (%s, 'product', %s, %s)
            """, (prospect_id, product.name, json.dumps({
                "description": product.description,
                "type": product.type,
                "price_cents": product.price_cents,
                "currency": product.currency,
                "interval": product.interval,
                "features": product.features,
                "recommended": product.recommended,
            })))

        # SEO
        seo = results["seo"]
        cur.execute("""
            INSERT INTO generated_content (prospect_id, content_type, title, body)
            VALUES (%s, 'seo', %s, %s)
        """, (prospect_id, seo.seo_title, json.dumps({
            "seo_title": seo.seo_title,
            "seo_description": seo.seo_description,
            "seo_keywords": seo.seo_keywords,
            "og_title": seo.og_title,
            "og_description": seo.og_description,
            "store_slug": seo.store_slug,
        })))

        # Colors
        colors = results["colors"]
        if colors:
            cur.execute("""
                INSERT INTO generated_content (prospect_id, content_type, title, body)
                VALUES (%s, 'colors', 'Brand Colors', %s)
            """, (prospect_id, json.dumps({
                "primary": colors.primary,
                "secondary": colors.secondary,
                "accent": colors.accent,
                "background": colors.background,
                "text": colors.text,
                "palette": colors.palette,
                "hero_bg": colors.primary,
            })))

        # Update prospect status
        cur.execute(
            "UPDATE prospects SET status = 'CONTENT_GENERATED' WHERE id = %s",
            (prospect_id,),
        )

    conn.commit()
    print(f"  Stored: bio, {len(results['blogs'])} blogs, {len(results['pricing'].products)} products, SEO, colors")
    print()


# ─── Step 5: Store Preview ────────────────────────────────────────────────────


def print_store_preview(profile: dict, results: dict):
    """Print a console summary of the generated store."""
    bio = results["bio"]
    seo = results["seo"]
    pricing = results["pricing"]
    colors = results.get("colors")
    blogs = results["blogs"]

    print("=" * 60)
    print("  STORE PREVIEW")
    print("=" * 60)
    print(f"  Store Name:    {profile['name']}")
    print(f"  URL:           {seo.store_slug}.joinkliq.io")
    print(f"  Tagline:       {bio.tagline}")
    print(f"  SEO Title:     {seo.seo_title}")
    if colors:
        print(f"  Brand Color:   {colors.primary}")
    print(f"\n  Bio:           {bio.short_bio[:100]}...")
    print(f"  Specialties:   {', '.join(bio.specialties)}")
    print(f"\n  Products ({len(pricing.products)}):")
    for p in pricing.products:
        sym = "$" if p.currency == "USD" else "£"
        interval = f"/{p.interval}" if p.interval else ""
        print(f"    - {p.name}: {sym}{p.price_cents/100:.2f}{interval}")
    print(f"\n  Blog Posts ({len(blogs)}):")
    for b in blogs:
        print(f"    - {b.blog_title}")
    print(f"\n  View full preview: http://localhost:8501/store_preview")
    print("=" * 60)
    print()


# ─── Step 6: CMS Dry Run ─────────────────────────────────────────────────────


def cms_dry_run(profile: dict, results: dict):
    """Log what would be created in the CMS."""
    seo = results["seo"]
    colors = results.get("colors")
    pricing = results["pricing"]
    blogs = results["blogs"]

    print("[Step 6] CMS Store Creation (DRY RUN)")
    print("  Would create in CMS MySQL (10.118.193.3):")
    print(f"    Application:        name='{profile['name']}'")
    print(f"    ApplicationSetting: web_url='{seo.store_slug}.joinkliq.io'")
    print(f"    ApplicationColor:   primary='{colors.primary if colors else '#1E81FF'}'")
    print(f"    Role:               'Coach Admin' (user_type=3)")
    print(f"    User:               email='{profile.get('email') or f'unclaimed@joinkliq.io'}'")
    print(f"    Products:           {len(pricing.products)} products (Draft)")
    print(f"    Pages:              1 About + {len(blogs)} blog posts (Draft)")
    print("  [SKIPPED - CMS MySQL not accessible locally]")
    print()


# ─── Step 7: Email Preview ───────────────────────────────────────────────────


def generate_email_preview(profile: dict, results: dict, prospect_id: int):
    """Generate the outreach email HTML and save to file."""
    from app.outreach.email_builder import build_outreach_email

    bio = results["bio"]
    seo = results["seo"]
    colors = results.get("colors")
    pricing = results["pricing"]
    blogs = results["blogs"]

    print("[Step 7] Email Preview")

    email = build_outreach_email(
        step=1,
        email=profile.get("email") or "coach@example.com",
        first_name=profile["name"].split()[0],
        store_name=profile["name"],
        platform="YouTube",
        claim_token=f"test-{prospect_id}-{int(time.time())}",
        primary_color=colors.primary if colors else "#1E81FF",
        tagline=bio.tagline,
        blog_count=len(blogs),
        product_count=len(pricing.products),
        store_url=f"https://{seo.store_slug}.joinkliq.io",
    )

    output_dir = os.path.join(PROJECT_ROOT, "output")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"email_preview_{seo.store_slug}.html")

    with open(output_path, "w") as f:
        f.write(email.html_content)

    print(f"  Subject: {email.subject}")
    print(f"  To: {email.to_email}")
    print(f"  HTML saved: {output_path}")
    print(f"  Open in browser: file://{os.path.abspath(output_path)}")
    print()


# ─── Main ─────────────────────────────────────────────────────────────────────


def print_summary(profile: dict, videos: list[dict], results: dict | None):
    """Print final pipeline summary."""
    print("=" * 60)
    print("  PIPELINE COMPLETE")
    print("=" * 60)
    print(f"  Coach:         {profile['name']}")
    print(f"  Platform:      YouTube")
    print(f"  Videos:        {len(videos)} scraped")
    transcripts = sum(1 for v in videos if v["transcript"])
    print(f"  Transcripts:   {transcripts} extracted")

    if results:
        print(f"  Bio:           Generated")
        print(f"  Blogs:         {len(results['blogs'])} generated")
        print(f"  Products:      {len(results['pricing'].products)} suggested")
        print(f"  SEO:           {results['seo'].store_slug}.joinkliq.io")
        print(f"  Colors:        {'Extracted' if results.get('colors') else 'Default'}")
        usage = results.get("token_usage", {})
        if usage:
            total = usage.get("total_tokens", 0)
            # Rough cost estimate (Sonnet: $3/M input + $15/M output)
            est_cost = (usage.get("input_tokens", 0) * 3 + usage.get("output_tokens", 0) * 15) / 1_000_000
            print(f"  Tokens:        {total:,} (~${est_cost:.2f})")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="KLIQ Growth Engine — End-to-End Pipeline Test",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("channel", help="YouTube channel (@handle, URL, or channel ID)")
    parser.add_argument("--max-videos", type=int, default=5, help="Max videos to scrape (default: 5)")
    parser.add_argument("--max-blogs", type=int, default=3, help="Max blogs to generate (default: 3)")
    parser.add_argument("--skip-ai", action="store_true", help="Skip AI generation (scraping only)")
    parser.add_argument("--skip-db", action="store_true", help="Skip database storage")
    args = parser.parse_args()

    print()
    print("=" * 60)
    print("  KLIQ Growth Engine — End-to-End Pipeline Test")
    print("=" * 60)

    # Step 0
    check_prerequisites(skip_db=args.skip_db, skip_ai=args.skip_ai)

    # Step 1
    profile, videos = scrape_youtube_channel(args.channel, max_videos=args.max_videos)

    if not videos:
        print("No videos found. Exiting.")
        sys.exit(1)

    # Step 2
    prospect_id = None
    conn = None
    if not args.skip_db:
        conn = get_db_connection()
        prospect_id = store_prospect(conn, profile)
        store_scraped_content(conn, prospect_id, videos)

    # Steps 3-4
    results = None
    if not args.skip_ai:
        results = run_ai_generation(profile, videos)

        if not args.skip_db and conn:
            store_generated_content(conn, prospect_id, results, videos)

    # Step 5
    if results:
        print_store_preview(profile, results)

    # Step 6
    if results:
        cms_dry_run(profile, results)

    # Step 7
    if results and prospect_id:
        try:
            generate_email_preview(profile, results, prospect_id)
        except Exception as e:
            print(f"[Step 7] Email preview failed: {e}")
            print("  (Email templates may not be set up yet)")

    # Summary
    print_summary(profile, videos, results)

    if conn:
        conn.close()


if __name__ == "__main__":
    main()
