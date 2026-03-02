# Scrapers

> Platform adapters and the discovery pipeline for finding coaches.

## Overview

The scraping layer discovers coaches on competitor platforms, scrapes their profiles, content, and pricing, and normalizes everything into a common data model. Each platform implements the `PlatformAdapter` interface. The `DiscoveryOrchestrator` coordinates multi-platform discovery with deduplication and cross-platform enrichment.

## Files

| File | Purpose |
|------|---------|
| `app/scrapers/base.py` | Abstract `PlatformAdapter`, data models |
| `app/scrapers/youtube.py` | YouTube Data API v3 adapter |
| `app/scrapers/skool.py` | Skool (Apify + Playwright fallback) |
| `app/scrapers/patreon.py` | Patreon API v2 adapter |
| `app/scrapers/website.py` | Generic website scraper (Playwright + BeautifulSoup) |
| `app/scrapers/onlyfans.py` | OnlyFans adapter (Playwright) |
| `app/scrapers/stan.py` | Stan.store adapter (Playwright) |
| `app/scrapers/instagram.py` | Stub (not implemented) |
| `app/scrapers/tiktok.py` | Stub (not implemented) |
| `app/scrapers/discovery.py` | `DiscoveryOrchestrator` — multi-platform coordination |
| `app/scrapers/color_extractor.py` | Extract brand colors from images |

## Base Classes

**File:** `app/scrapers/base.py`

### `ScrapedProfile`

**File:** `app/scrapers/base.py:26`

Normalized profile data from any platform.

| Field | Type | Description |
|-------|------|-------------|
| `platform` | Platform | Source platform |
| `platform_id` | str | Platform-specific ID |
| `name` | str | Display name |
| `bio` | str | Profile bio text |
| `profile_image_url` | str | Avatar URL |
| `banner_image_url` | str | Banner/header image |
| `email` | str? | Extracted email |
| `website_url` | str? | Personal website |
| `social_links` | dict | Cross-platform links |
| `follower_count` | int | Followers/subscribers |
| `niche_tags` | list[str] | Detected niches |
| `raw_data` | dict | Full API response |

### `ScrapedContent`

**File:** `app/scrapers/base.py:48`

A piece of content (video, post, course).

| Field | Type | Description |
|-------|------|-------------|
| `content_type` | str | "video", "post", "course", "blog" |
| `title` | str | Content title |
| `body` | str | Transcript or full text |
| `view_count` | int | Views |
| `engagement_count` | int | Likes/comments |

### `ScrapedPricing`

**File:** `app/scrapers/base.py:68`

A pricing tier from any platform.

| Field | Type | Description |
|-------|------|-------------|
| `tier_name` | str | Tier display name |
| `price_amount` | float | Price value |
| `currency` | str | Default: "USD" |
| `interval` | str | "month", "year", "one_time" |
| `benefits` | list[str] | Feature list |
| `member_count` | int | Current members |

### `PlatformAdapter` (ABC)

**File:** `app/scrapers/base.py:82`

Interface that every platform must implement:

| Method | Signature | Description |
|--------|-----------|-------------|
| `platform` | property → Platform | Platform enum value |
| `discover_coaches` | (queries, max_results) → list[ScrapedProfile] | Search for coaches |
| `scrape_profile` | (platform_id) → ScrapedProfile | Full profile details |
| `scrape_content` | (platform_id, max_items) → list[ScrapedContent] | Recent content |
| `scrape_pricing` | (platform_id) → list[ScrapedPricing] | Pricing tiers |
| `extract_email` | (profile) → str? | Find email in bio (default: regex) |
| `extract_social_links` | (text) → dict | Parse social URLs from text |

## Platform Adapters

### YouTubeAdapter

**File:** `app/scrapers/youtube.py`

Uses the Google YouTube Data API v3.

- **Discovery:** Search for channels matching queries (100 units/call)
- **Profile:** Channel details (1 unit)
- **Content:** Latest videos + transcripts via `youtube-transcript-api` (free)
- **Quota:** 10,000 units/day = ~50 coaches/day capacity
- **Niche detection:** fitness, yoga, nutrition, strength, cardio, pilates, wellness, crossfit, calisthenics, martial_arts

### SkoolAdapter

**File:** `app/scrapers/skool.py`

Uses Apify Skool Scraper actor with Playwright fallback.

- **Discovery:** Search via Apify actor
- **Profile:** Playwright browser scraping
- **Pricing:** Detects tier structure and member counts
- **Content:** Community posts

### PatreonAdapter

**File:** `app/scrapers/patreon.py`

Uses Patreon API v2.

- **Pricing:** Detailed tier info with member counts
- **Profile:** Creator profiles

### WebsiteAdapter

**File:** `app/scrapers/website.py`

Uses Playwright + BeautifulSoup.

- **Scraping:** Landing pages, pricing tables
- **Email:** Regex extraction from page content

### OnlyFansAdapter

**File:** `app/scrapers/onlyfans.py`

Uses Playwright (requires account login).

### StanAdapter

**File:** `app/scrapers/stan.py`

Uses Playwright + Google site-search for discovery.

- **Discovery:** Google `site:stan.store` search, then enriches top results
- **Profile:** Creator page scraping (name, bio, social links, products)
- **Content:** Product cards (digital products, courses, memberships, coaching)
- **Pricing:** Per-product pricing extraction
- **Competitor:** Direct KLIQ competitor — creator commerce platform for digital products

### Color Extractor

**File:** `app/scrapers/color_extractor.py`

Extracts dominant brand colors from profile images using ColorThief.

```python
@dataclass
class BrandColors:
    primary: str     # Hex color
    secondary: str
    accent: str
    background: str
    text: str
    palette: list[str]
```

### `extract_colors_from_url(image_url) → BrandColors`
Downloads image and extracts dominant colors.

## Discovery Orchestrator

**File:** `app/scrapers/discovery.py`

Coordinates multi-platform discovery.

### Key Functions

#### `DiscoveryOrchestrator.discover(queries, platforms, max_per_platform) → list[EnrichedProspect]`

1. Runs discovery on each adapter in parallel
2. Cross-platform enrichment (YouTube → Skool/Patreon/website chain)
3. Deduplication by email, URL, and fuzzy name match (threshold: 0.85)
4. Priority sorting: email presence > follower count

### `EnrichedProspect`

A prospect assembled from data across all platforms:
- `primary_profile` — Main platform profile
- `all_profiles` — All platform profiles
- `all_content` — All scraped content
- `all_pricing` — All pricing tiers
- `name`, `email`, `bio`, `profile_image_url`, `social_links`, `brand_colors`

## Data Flow

```
Search queries → Adapters → ScrapedProfile[] → DiscoveryOrchestrator
    │                                              │
    │                                              ├── Deduplication
    │                                              ├── Cross-platform enrichment
    │                                              └── Priority sort
    │                                              │
    └──────────────────────────────────────────────→ EnrichedProspect[]
                                                        │
                                                        ▼
                                                    Database (Prospect rows)
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `YOUTUBE_API_KEY` | — | Google API key for YouTube |
| `APIFY_API_TOKEN` | — | Apify API token for Skool |
| `PATREON_CLIENT_ID` | — | Patreon OAuth client |
| `PATREON_CLIENT_SECRET` | — | Patreon OAuth secret |
| `YOUTUBE_MAX_DAILY_UNITS` | 10000 | Daily API quota |
| `SCRAPE_DELAY_SECONDS` | 2 | Rate limiting delay |
| `MAX_CONCURRENT_SCRAPES` | 5 | Parallelism cap |
