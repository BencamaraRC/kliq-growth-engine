# Database

> PostgreSQL models for the Growth Engine and MySQL integration with RCWL-CMS.

## Overview

The Growth Engine uses two databases. Its own PostgreSQL database stores prospects, scraped data, AI-generated content, and campaign tracking. It also writes directly to the RCWL-CMS MySQL database to create stores (applications, users, products, pages).

## Enums

**File:** `app/db/models.py:31-65`

| Enum | Values |
|------|--------|
| `Platform` | YOUTUBE, SKOOL, PATREON, WEBSITE, TIKTOK, INSTAGRAM, ONLYFANS, KAJABI |
| `ProspectStatus` | DISCOVERED, SCRAPED, CONTENT_GENERATED, STORE_CREATED, EMAIL_SENT, CLAIMED, REJECTED |
| `CampaignStatus` | DRAFT, ACTIVE, PAUSED, COMPLETED |
| `EmailStatus` | PENDING, SENT, OPENED, CLICKED, BOUNCED, UNSUBSCRIBED |

## Growth Engine Models (PostgreSQL)

### `Prospect`

**File:** `app/db/models.py:71-128` | **Table:** `prospects`

The central entity — a coach/creator discovered on a competitor platform.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `status` | Enum(ProspectStatus) | Default: DISCOVERED |
| `name` | String(255) | Display name |
| `email` | String(255) | Unique, nullable |
| `first_name` | String(100) | Nullable |
| `last_name` | String(100) | Nullable |
| `primary_platform` | Enum(Platform) | Source platform |
| `primary_platform_id` | String(255) | Platform-specific ID |
| `primary_platform_url` | String(500) | Nullable |
| `bio` | Text | Nullable |
| `profile_image_url` | String(500) | Nullable |
| `banner_image_url` | String(500) | Nullable |
| `website_url` | String(500) | Nullable |
| `social_links` | JSON | Nullable |
| `niche_tags` | JSON | List of strings, nullable |
| `location` | String(255) | Nullable |
| `follower_count` | Integer | Default: 0 |
| `subscriber_count` | Integer | Default: 0 |
| `content_count` | Integer | Default: 0 |
| `brand_colors` | JSON | List of hex strings, nullable |
| `kliq_application_id` | Integer | CMS app ID, set after store creation |
| `kliq_store_url` | String(500) | Set after store creation |
| `claim_token` | String(255) | JWT for claim flow |
| `discovered_at` | DateTime | Server default: now() |
| `store_created_at` | DateTime | Nullable |
| `claimed_at` | DateTime | Nullable |
| `created_at` | DateTime | Server default: now() |
| `updated_at` | DateTime | Auto-updates on change |

**Relationships:** `scraped_content`, `scraped_pricing`, `generated_content`, `campaign_events`, `platform_profiles`

### `PlatformProfile`

**File:** `app/db/models.py:131-144` | **Table:** `platform_profiles`

A prospect's profile on a specific platform (supports multi-platform enrichment).

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `prospect_id` | FK → prospects.id | |
| `platform` | Enum(Platform) | |
| `platform_id` | String(255) | Platform-specific ID |
| `platform_url` | String(500) | Nullable |
| `raw_data` | JSON | Full API response, nullable |
| `scraped_at` | DateTime | Server default: now() |

### `ScrapedContentRecord`

**File:** `app/db/models.py:147-168` | **Table:** `scraped_content`

A piece of content (video, post, course) scraped from a platform.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `prospect_id` | FK → prospects.id | |
| `platform` | Enum(Platform) | |
| `content_type` | String(50) | video, post, course, blog |
| `title` | String(500) | Nullable |
| `description` | Text | Nullable |
| `body` | Text | Transcript or full text, nullable |
| `url` | String(500) | Nullable |
| `thumbnail_url` | String(500) | Nullable |
| `published_at` | DateTime | Nullable |
| `view_count` | Integer | Default: 0 |
| `engagement_count` | Integer | Default: 0 |
| `tags` | JSON | Nullable |
| `raw_data` | JSON | Nullable |
| `scraped_at` | DateTime | Server default: now() |

### `ScrapedPricingRecord`

**File:** `app/db/models.py:171-188` | **Table:** `scraped_pricing`

A pricing tier scraped from a competitor platform.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `prospect_id` | FK → prospects.id | |
| `platform` | Enum(Platform) | |
| `tier_name` | String(255) | |
| `price_amount` | Float | |
| `currency` | String(10) | Default: "USD" |
| `interval` | String(20) | Default: "month" |
| `description` | Text | Nullable |
| `benefits` | JSON | Nullable |
| `member_count` | Integer | Default: 0 |
| `scraped_at` | DateTime | Server default: now() |

### `GeneratedContent`

**File:** `app/db/models.py:191-207` | **Table:** `generated_content`

AI-generated content for a prospect's KLIQ store.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `prospect_id` | FK → prospects.id | |
| `content_type` | String(50) | bio, blog, product, seo, color |
| `title` | String(500) | Nullable |
| `body` | Text | JSON string with full content, nullable |
| `content_metadata` | JSON | Nullable |
| `source_content_id` | FK → scraped_content.id | Nullable |
| `generated_at` | DateTime | Server default: now() |

### `Campaign`

**File:** `app/db/models.py:210-229` | **Table:** `campaigns`

An outreach campaign targeting discovered coaches.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `name` | String(255) | |
| `status` | Enum(CampaignStatus) | Default: DRAFT |
| `platform_filter` | Enum(Platform) | Nullable |
| `niche_filter` | JSON | Nullable |
| `min_followers` | Integer | Default: 0 |
| `email_sequence` | JSON | Nullable |
| `created_at` | DateTime | Server default: now() |
| `updated_at` | DateTime | Auto-updates |

**Relationships:** `events`

### `CampaignEvent`

**File:** `app/db/models.py:232-250` | **Table:** `campaign_events`

Tracks email sends, opens, clicks, and claims for a campaign.

| Column | Type | Notes |
|--------|------|-------|
| `id` | Integer PK | Auto-increment |
| `campaign_id` | FK → campaigns.id | |
| `prospect_id` | FK → prospects.id | |
| `step` | Integer | 1=store_ready, 2=reminder_1, 3=reminder_2, 4=claimed |
| `email_status` | Enum(EmailStatus) | Default: PENDING |
| `sent_at` | DateTime | Nullable |
| `opened_at` | DateTime | Nullable |
| `clicked_at` | DateTime | Nullable |
| `brevo_message_id` | String(255) | Nullable |

## CMS Models (MySQL)

**File:** `app/cms/models.py`

These mirror the RCWL-CMS Laravel tables. The Growth Engine writes to them directly to create stores.

| Model | Table | Purpose |
|-------|-------|---------|
| `Application` | applications | A KLIQ app/store instance |
| `ApplicationSetting` | application_settings | App config (name, SEO, etc.) |
| `ApplicationColor` | application_colors | Brand color scheme |
| `ApplicationFeatureSetup` | application_feature_setups | Feature toggles |
| `AudioSetting` | audio_settings | Audio preferences |
| `CMSUser` | users | Coach login account |
| `UserDetail` | user_details | Profile metadata |
| `UserApplication` | user_applications | User-app relationship |
| `UserRole` | user_roles | Role assignment |
| `Role` | roles | Permission role definition |
| `ApplicationRole` | application_roles | App-role binding |
| `PermissionModule` | permission_modules | Feature modules |
| `PermissionReference` | permission_references | Individual permissions |
| `PermissionGroup` | permission_groups | Permission-role mapping |
| `EmailTemplate` | email_templates | Transactional email templates |
| `EmailTemplateType` | email_template_types | Template categories |
| `ReferralPoint` | referral_points | Referral program config |
| `Product` | products | Subscription/one-time products |
| `Page` | pages | About pages, blog posts |

## Session Factories

**File:** `app/db/session.py`

```python
engine       # PostgreSQL async engine (pool_size=10)
async_session  # PostgreSQL session maker
cms_engine   # MySQL async engine (pool_size=5)
cms_session  # MySQL session maker

get_db()     # FastAPI dependency → PostgreSQL session
get_cms_db() # FastAPI dependency → MySQL session
```

## Migrations

Managed by Alembic. Initial migration: `migrations/versions/8dd1d61b8349_initial_growth_engine_schema.py`.

```bash
alembic upgrade head    # Apply all migrations
alembic revision -m "description" --autogenerate  # Generate new migration
```
