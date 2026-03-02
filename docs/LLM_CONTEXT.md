# KLIQ Growth Engine — LLM Context

## Project

- **Type:** Automated coach acquisition pipeline
- **Stack:** FastAPI + Celery + Redis + PostgreSQL + MySQL + Claude AI + Brevo + Streamlit
- **Python:** 3.11+
- **Purpose:** Discover fitness/wellness coaches on competitor platforms, generate AI-powered KLIQ webstores, run email outreach to get them to claim their stores
- **Status:** Active development (v0.1.0, created Feb 2026)
- **Root:** `~/projects/kliq-growth-engine/`
- **Run API:** `uvicorn app.main:app --reload --port 8000`
- **Run Workers:** `celery -A app.workers.celery_app worker -l info -B`
- **Run Dashboard:** `streamlit run dashboard/app.py`
- **Run Tests:** `pytest`

## Architecture

### Databases
- **PostgreSQL** (asyncpg, pool_size=10): Growth Engine data — prospects, scraped content, generated content, campaigns
- **MySQL** (aiomysql, pool_size=5): RCWL-CMS — applications, users, products, pages. Growth Engine writes directly to CMS tables to create stores.

### Services
- **FastAPI** (port 8000): REST API + HTML pages (claim/preview)
- **Celery** (Redis broker): Async task processing for scraping, AI generation, store creation, email
- **Streamlit**: Dashboard for monitoring and manual pipeline triggers

### Key Patterns
- **Dual-DB writes:** Growth Engine DB (own data) + CMS DB (store creation)
- **Async bridge:** Celery tasks use `_run_async()` to run async code in sync context
- **Task chaining:** `chain(generate_content_task.si(), create_store_task.si())`
- **Buffered analytics:** BigQuery events buffered (50 events / 30s flush)
- **Jinja2 prompts:** AI prompts are Jinja2 templates in `app/ai/prompts/`
- **Jinja2 emails:** HTML email templates in `app/outreach/templates/`

### Pipeline Stages
```
DISCOVERED → SCRAPED → CONTENT_GENERATED → STORE_CREATED → EMAIL_SENT → CLAIMED | REJECTED
```

## Module Map

| File | Purpose | Key Exports |
|------|---------|-------------|
| `app/main.py` | FastAPI app, router mounting | `app` |
| `app/config.py` | Settings from .env | `settings` |
| `app/db/models.py` | PostgreSQL models | `Prospect`, `PlatformProfile`, `ScrapedContentRecord`, `ScrapedPricingRecord`, `GeneratedContent`, `Campaign`, `CampaignEvent`, `Platform`, `ProspectStatus`, `CampaignStatus`, `EmailStatus` |
| `app/db/session.py` | Async session factories | `engine`, `async_session`, `cms_engine`, `cms_session`, `get_db()`, `get_cms_db()` |
| `app/api/prospects.py` | Prospect CRUD endpoints | `router`, `ProspectResponse`, `ProspectListResponse` |
| `app/api/campaigns.py` | Campaign CRUD endpoints | `router`, `CampaignCreate`, `CampaignResponse` |
| `app/api/pipeline.py` | Pipeline trigger endpoints | `router`, `DiscoverRequest`, `ScrapeRequest`, `PipelineStatusResponse` |
| `app/api/webhooks.py` | Claim + Brevo webhooks | `router`, `ClaimRequest`, `ClaimResponse` |
| `app/ai/client.py` | Claude API wrapper | `AIClient`, `MODEL_SONNET`, `MODEL_OPUS` |
| `app/ai/bio_generator.py` | Coach bio generation | `generate_bio()`, `GeneratedBio` |
| `app/ai/blog_generator.py` | Blog from transcripts | `generate_blog()`, `generate_blogs_batch()`, `GeneratedBlog` |
| `app/ai/pricing_analyzer.py` | Pricing recommendations | `analyze_pricing()`, `PricingAnalysis`, `SuggestedProduct` |
| `app/ai/seo_generator.py` | SEO metadata generation | `generate_seo()`, `GeneratedSEO` |
| `app/scrapers/base.py` | Abstract adapter + data models | `PlatformAdapter`, `ScrapedProfile`, `ScrapedContent`, `ScrapedPricing` |
| `app/scrapers/youtube.py` | YouTube Data API v3 | `YouTubeAdapter` |
| `app/scrapers/skool.py` | Skool (Apify + Playwright) | `SkoolAdapter` |
| `app/scrapers/patreon.py` | Patreon API v2 | `PatreonAdapter` |
| `app/scrapers/website.py` | Generic website scraper | `WebsiteAdapter` |
| `app/scrapers/onlyfans.py` | OnlyFans (Playwright) | `OnlyFansAdapter` |
| `app/scrapers/instagram.py` | Stub | — |
| `app/scrapers/tiktok.py` | Stub | — |
| `app/scrapers/discovery.py` | Multi-platform orchestrator | `DiscoveryOrchestrator`, `EnrichedProspect` |
| `app/scrapers/color_extractor.py` | Brand color extraction | `extract_colors_from_url()`, `BrandColors` |
| `app/cms/models.py` | CMS MySQL table models | `Application`, `ApplicationSetting`, `ApplicationColor`, `CMSUser`, `Role`, `Product`, `Page`, etc. |
| `app/cms/store_builder.py` | Complete store creation | `build_store()`, `StoreCreationResult`, `STATUS_INACTIVE`, `STATUS_ACTIVE` |
| `app/cms/products.py` | Product creation | `create_products()` |
| `app/cms/content.py` | Page creation | `create_about_page()`, `create_blog_pages()` |
| `app/cms/media.py` | S3 image uploads | `upload_image_from_url()`, `upload_store_images()` |
| `app/workers/celery_app.py` | Celery config + beat schedule | `celery_app` |
| `app/workers/scrape_tasks.py` | Discovery + scrape tasks | `discover_coaches_task`, `scrape_single_coach_task` |
| `app/workers/ai_tasks.py` | AI generation task | `generate_content_task` |
| `app/workers/pipeline_task.py` | Full pipeline chain | `full_pipeline_task` |
| `app/workers/populate_tasks.py` | CMS store creation task | `create_store_task` |
| `app/workers/outreach_tasks.py` | Email sending tasks | `send_outreach_email_task`, `process_outreach_queue` |
| `app/outreach/campaign_manager.py` | 4-step email lifecycle | `process_outreach()`, `send_claim_confirmation()` |
| `app/outreach/email_builder.py` | Email template rendering | `build_outreach_email()`, `BuiltEmail`, `STEPS` |
| `app/outreach/brevo_client.py` | Brevo API client | `BrevoClient`, `EmailResult` |
| `app/outreach/claim_handler.py` | Claim validation + activation | `validate_claim_token()`, `activate_store()`, `ClaimError` |
| `app/outreach/tracking.py` | Brevo webhook processing | `process_brevo_event()`, `EVENT_MAP` |
| `app/preview/router.py` | Store preview route | `router` |
| `app/preview/renderer.py` | HTML preview rendering | `render_store_preview()` |
| `app/preview/queries.py` | Preview data queries | `get_prospect_by_id()`, `get_generated_content()` |
| `app/claim/router.py` | Claim flow routes | `router` |
| `app/claim/renderer.py` | Claim page rendering | `render_claim_page()`, `render_welcome_page()`, `render_error_page()`, `render_already_claimed_page()` |
| `app/claim/queries.py` | Claim data queries | `get_prospect_by_token()`, `get_content_counts()`, `get_auto_login_token()` |
| `app/events/bigquery.py` | Buffered event logging | `BigQueryLogger`, `GrowthEvent`, `log_event()`, `get_bq_logger()` |
| `app/events/slack.py` | Slack notifications | `notify_pipeline_error()`, `notify_store_claimed()`, `notify_daily_digest()` |
| `dashboard/app.py` | Dashboard home page | — |
| `dashboard/theme.py` | KLIQ design system + auth | `inject_kliq_theme()`, `sidebar_nav()`, `apply_plotly_theme()`, `CHART_COLORS` |
| `dashboard/data.py` | SQL queries for dashboard | `get_kpi_summary()`, `get_funnel_data()`, `get_platform_breakdown()`, `get_daily_activity()`, `get_niche_distribution()` |
| `dashboard/pages/profiles.py` | Prospect list page | — |
| `dashboard/pages/profile_detail.py` | Prospect detail page | — |
| `dashboard/pages/pipeline.py` | Pipeline trigger page | — |
| `dashboard/pages/campaigns.py` | Campaign management page | — |
| `dashboard/pages/store_preview.py` | Visual store preview | — |

## API Endpoints

| Method | Path | Handler | File:Line | Description |
|--------|------|---------|-----------|-------------|
| GET | `/health` | `health()` | `main.py:33` | Health check |
| GET | `/api/prospects/` | `list_prospects()` | `api/prospects.py:35` | List prospects (filter: status, platform, limit, offset) |
| GET | `/api/prospects/{id}` | `get_prospect()` | `api/prospects.py:68` | Get single prospect |
| GET | `/api/campaigns/` | `list_campaigns()` | `api/campaigns.py:32` | List all campaigns |
| POST | `/api/campaigns/` | `create_campaign()` | `api/campaigns.py:38` | Create campaign (body: name, platform_filter?, niche_filter?, min_followers?) |
| POST | `/api/campaigns/{id}/activate` | `activate_campaign()` | `api/campaigns.py:53` | Set campaign ACTIVE |
| POST | `/api/campaigns/{id}/pause` | `pause_campaign()` | `api/campaigns.py:66` | Set campaign PAUSED |
| POST | `/api/pipeline/discover` | `trigger_discovery()` | `api/pipeline.py:35` | Queue discovery (body: platforms, search_queries, max_per_platform) |
| POST | `/api/pipeline/scrape` | `trigger_scrape()` | `api/pipeline.py:52` | Queue single scrape (body: platform, platform_id) |
| POST | `/api/pipeline/run/{id}` | `trigger_full_pipeline()` | `api/pipeline.py:64` | Queue full pipeline for prospect |
| GET | `/api/pipeline/status/{task_id}` | `get_task_status()` | `api/pipeline.py:73` | Poll Celery task status |
| POST | `/api/webhooks/claim` | `claim_store()` | `api/webhooks.py:31` | API claim (body: token, password) |
| POST | `/api/webhooks/brevo` | `brevo_webhook()` | `api/webhooks.py:74` | Brevo email event webhook |
| GET | `/preview/{id}` | `preview_store()` | `preview/router.py:15` | HTML store preview (public) |
| GET | `/claim` | `claim_page()` | `claim/router.py:24` | Claim page with password form |
| POST | `/claim` | `claim_submit()` | `claim/router.py:50` | Claim form submission |
| GET | `/welcome` | `welcome_page()` | `claim/router.py:117` | Post-claim onboarding |

## Database Schema

### Enums

| Enum | Values |
|------|--------|
| `Platform` | YOUTUBE, SKOOL, PATREON, WEBSITE, TIKTOK, INSTAGRAM, ONLYFANS, KAJABI |
| `ProspectStatus` | DISCOVERED, SCRAPED, CONTENT_GENERATED, STORE_CREATED, EMAIL_SENT, CLAIMED, REJECTED |
| `CampaignStatus` | DRAFT, ACTIVE, PAUSED, COMPLETED |
| `EmailStatus` | PENDING, SENT, OPENED, CLICKED, BOUNCED, UNSUBSCRIBED |

### prospects

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| status | Enum(ProspectStatus) | default DISCOVERED |
| name | String(255) | |
| email | String(255) | unique, nullable |
| first_name | String(100) | nullable |
| last_name | String(100) | nullable |
| primary_platform | Enum(Platform) | |
| primary_platform_id | String(255) | |
| primary_platform_url | String(500) | nullable |
| bio | Text | nullable |
| profile_image_url | String(500) | nullable |
| banner_image_url | String(500) | nullable |
| website_url | String(500) | nullable |
| social_links | JSON | nullable |
| niche_tags | JSON | nullable |
| location | String(255) | nullable |
| follower_count | Integer | default 0 |
| subscriber_count | Integer | default 0 |
| content_count | Integer | default 0 |
| brand_colors | JSON | nullable |
| kliq_application_id | Integer | nullable |
| kliq_store_url | String(500) | nullable |
| claim_token | String(255) | nullable |
| discovered_at | DateTime | server_default now() |
| store_created_at | DateTime | nullable |
| claimed_at | DateTime | nullable |
| created_at | DateTime | server_default now() |
| updated_at | DateTime | onupdate now() |

Relationships: scraped_content, scraped_pricing, generated_content, campaign_events, platform_profiles

### platform_profiles

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| prospect_id | Integer | FK → prospects.id |
| platform | Enum(Platform) | |
| platform_id | String(255) | |
| platform_url | String(500) | nullable |
| raw_data | JSON | nullable |
| scraped_at | DateTime | server_default now() |

### scraped_content

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| prospect_id | Integer | FK → prospects.id |
| platform | Enum(Platform) | |
| content_type | String(50) | video/post/course/blog |
| title | String(500) | nullable |
| description | Text | nullable |
| body | Text | transcript/full text, nullable |
| url | String(500) | nullable |
| thumbnail_url | String(500) | nullable |
| published_at | DateTime | nullable |
| view_count | Integer | default 0 |
| engagement_count | Integer | default 0 |
| tags | JSON | nullable |
| raw_data | JSON | nullable |
| scraped_at | DateTime | server_default now() |

### scraped_pricing

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| prospect_id | Integer | FK → prospects.id |
| platform | Enum(Platform) | |
| tier_name | String(255) | |
| price_amount | Float | |
| currency | String(10) | default "USD" |
| interval | String(20) | default "month" |
| description | Text | nullable |
| benefits | JSON | nullable |
| member_count | Integer | default 0 |
| scraped_at | DateTime | server_default now() |

### generated_content

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| prospect_id | Integer | FK → prospects.id |
| content_type | String(50) | bio/blog/product/seo/color |
| title | String(500) | nullable |
| body | Text | JSON string, nullable |
| content_metadata | JSON | nullable |
| source_content_id | Integer | FK → scraped_content.id, nullable |
| generated_at | DateTime | server_default now() |

### campaigns

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| name | String(255) | |
| status | Enum(CampaignStatus) | default DRAFT |
| platform_filter | Enum(Platform) | nullable |
| niche_filter | JSON | nullable |
| min_followers | Integer | default 0 |
| email_sequence | JSON | nullable |
| created_at | DateTime | server_default now() |
| updated_at | DateTime | onupdate now() |

### campaign_events

| Column | Type | Constraints |
|--------|------|-------------|
| id | Integer | PK, auto |
| campaign_id | Integer | FK → campaigns.id |
| prospect_id | Integer | FK → prospects.id |
| step | Integer | 1=store_ready, 2=reminder_1, 3=reminder_2, 4=claimed |
| email_status | Enum(EmailStatus) | default PENDING |
| sent_at | DateTime | nullable |
| opened_at | DateTime | nullable |
| clicked_at | DateTime | nullable |
| brevo_message_id | String(255) | nullable |

## Function Reference

### AI Client (`app/ai/client.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `AIClient.__init__` | 34 | `(api_key: str \| None)` | Init Anthropic client |
| `AIClient.generate` | 39 | `(prompt, system, model, max_tokens, temperature) → str` | Text completion with retry |
| `AIClient.generate_json` | 97 | `(prompt, system, model, max_tokens, temperature) → dict` | JSON output with parse recovery |
| `AIClient._parse_json` | 152 | `(text) → dict` | Strip markdown fences, parse JSON |
| `AIClient.usage_summary` | 166 | `→ dict` | Cumulative token counts |

### Bio Generator (`app/ai/bio_generator.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `generate_bio` | 30 | `(client, name, platform, bio, niche_tags, follower_count, content_count, content_titles) → GeneratedBio` | Generate tagline, bios, specialties |

### Blog Generator (`app/ai/blog_generator.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `generate_blog` | 35 | `(client, coach_name, title, transcript, description, view_count, video_url) → GeneratedBlog \| None` | Single blog from transcript |
| `generate_blogs_batch` | 100 | `(client, coach_name, videos, max_blogs=5) → list[GeneratedBlog]` | Batch blogs from top videos |

### Pricing Analyzer (`app/ai/pricing_analyzer.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `analyze_pricing` | 39 | `(client, name, niche_tags, follower_count, pricing_tiers, content_types) → PricingAnalysis` | Suggest KLIQ products |
| `_default_products` | 109 | `(name) → list[SuggestedProduct]` | Fallback Community + Premium products |

### SEO Generator (`app/ai/seo_generator.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `generate_seo` | 32 | `(client, name, store_name, tagline, specialties, niche_tags, location, content_titles) → GeneratedSEO` | SEO titles, descriptions, slug |
| `_generate_slug` | 93 | `(name) → str` | Slug from name |
| `_sanitize_slug` | 98 | `(slug) → str` | URL-safe slug (max 50 chars) |

### Scraper Base (`app/scrapers/base.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `PlatformAdapter.discover_coaches` | 97 | `(queries, max_results) → list[ScrapedProfile]` | Abstract: search for coaches |
| `PlatformAdapter.scrape_profile` | 114 | `(platform_id) → ScrapedProfile` | Abstract: full profile |
| `PlatformAdapter.scrape_content` | 119 | `(platform_id, max_items) → list[ScrapedContent]` | Abstract: recent content |
| `PlatformAdapter.scrape_pricing` | 128 | `(platform_id) → list[ScrapedPricing]` | Abstract: pricing tiers |
| `PlatformAdapter.extract_email` | 132 | `(profile) → str \| None` | Regex email from bio |
| `PlatformAdapter.extract_social_links` | 147 | `(text) → dict` | Parse social URLs |

### Store Builder (`app/cms/store_builder.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `build_store` | 72 | `(session, name, email, first_name, last_name, ...) → StoreCreationResult` | Full CMS store bootstrap |

### Products (`app/cms/products.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `create_products` | 17 | `(session, application_id, products, currency_id) → list[int]` | Create draft products |

### Content (`app/cms/content.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `create_about_page` | 18 | `(session, application_id, long_bio, tagline, profile_image_url) → int` | Create About page |
| `create_blog_pages` | 55 | `(session, application_id, blogs) → list[int]` | Create blog pages |

### Media (`app/cms/media.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `upload_image_from_url` | 24 | `(image_url, s3_key, content_type) → str \| None` | Download + upload to S3 |
| `upload_store_images` | — | `(application_id, profile_image_url, banner_image_url) → dict` | Upload both store images |

### Campaign Manager (`app/outreach/campaign_manager.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `process_outreach` | 33 | `(session) → dict` | Process all pending emails |
| `send_claim_confirmation` | 81 | `(session, prospect)` | Send Step 4 email |

### Email Builder (`app/outreach/email_builder.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `build_outreach_email` | 57 | `(step, email, first_name, store_name, ...) → BuiltEmail` | Build personalized email |

### Brevo Client (`app/outreach/brevo_client.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `BrevoClient.send_email` | 39 | `(to_email, to_name, subject, html_content, tags, params) → EmailResult` | Send via Brevo API |

### Claim Handler (`app/outreach/claim_handler.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `validate_claim_token` | 31 | `(growth_db, token) → Prospect` | Validate token, raise ClaimError |
| `activate_store` | 54 | `(cms_db, growth_db, prospect, password) → dict` | Activate store in CMS |

### Tracking (`app/outreach/tracking.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `process_brevo_event` | 28 | `(session, payload) → str` | Process webhook event |

### BigQuery (`app/events/bigquery.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `BigQueryLogger.log` | 87 | `(event)` | Buffer an event |
| `BigQueryLogger.log_event` | 94 | `(event_type, **kwargs)` | Convenience logger |
| `BigQueryLogger.flush` | 116 | `()` | Flush buffer to BQ |
| `log_event` | 172 | `(event_type, **kwargs)` | Module-level convenience |

### Slack (`app/events/slack.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `notify_pipeline_error` | 54 | `(stage, prospect_id, error)` | Alert on failure |
| `notify_store_claimed` | 87 | `(prospect_name, email, platform, application_id)` | Celebrate conversion |
| `notify_daily_digest` | 115 | `(prospects_discovered, stores_created, emails_sent, claims, errors)` | Daily summary |

### Celery Tasks (`app/workers/`)
| Task | File:Line | Signature | Description |
|------|-----------|-----------|-------------|
| `discover_coaches_task` | `scrape_tasks.py:20` | `(platforms, search_queries, max_per_platform)` | Find coaches on platforms |
| `scrape_single_coach_task` | `scrape_tasks.py:116` | `(platform, platform_id)` | Scrape one coach |
| `generate_content_task` | `ai_tasks.py:41` | `(prospect_id)` | Generate all AI content |
| `create_store_task` | `populate_tasks.py:41` | `(prospect_id)` | Build CMS webstore |
| `full_pipeline_task` | `pipeline_task.py:15` | `(prospect_id)` | Chain: AI → store |
| `send_outreach_email_task` | `outreach_tasks.py:31` | `(prospect_id, step, campaign_id)` | Send one email |
| `process_outreach_queue` | `outreach_tasks.py:89` | `()` | Find + send pending emails |

### Dashboard Data (`dashboard/data.py`)
| Function | Line | Signature | Description |
|----------|------|-----------|-------------|
| `get_kpi_summary` | 23 | `() → dict` | Top-level KPI metrics |
| `get_funnel_data` | 59 | `() → DataFrame` | Status distribution |
| `get_platform_breakdown` | 81 | `() → DataFrame` | Platform distribution |
| `get_niche_distribution` | 95 | `() → DataFrame` | Niche tag frequency |
| `get_daily_activity` | — | `(days) → DataFrame` | Daily counts |

## Configuration

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_ENV` | str | `development` | Environment |
| `APP_DEBUG` | bool | `True` | Debug mode |
| `APP_PORT` | int | `8000` | Server port |
| `APP_BASE_URL` | str | `http://localhost:8000` | Base URL for links |
| `DATABASE_URL` | str | `postgresql+asyncpg://...` | Growth Engine PostgreSQL |
| `CMS_DATABASE_URL` | str | `mysql+aiomysql://...` | RCWL-CMS MySQL |
| `REDIS_URL` | str | `redis://localhost:6379/0` | Celery broker/backend |
| `ANTHROPIC_API_KEY` | str | `""` | Claude API key |
| `YOUTUBE_API_KEY` | str | `""` | YouTube Data API v3 |
| `APIFY_API_TOKEN` | str | `""` | Skool scraper |
| `PATREON_CLIENT_ID` | str | `""` | Patreon OAuth |
| `PATREON_CLIENT_SECRET` | str | `""` | Patreon OAuth |
| `BREVO_API_KEY` | str | `""` | Email sending |
| `BREVO_SENDER_EMAIL` | str | `growth@joinkliq.io` | From address |
| `BREVO_SENDER_NAME` | str | `KLIQ Growth Team` | From name |
| `AWS_ACCESS_KEY_ID` | str | `""` | S3 media uploads |
| `AWS_SECRET_ACCESS_KEY` | str | `""` | S3 secret |
| `AWS_S3_BUCKET` | str | `dev-rcwl-assets` | S3 bucket |
| `AWS_S3_REGION` | str | `eu-west-1` | S3 region |
| `GCP_PROJECT_ID` | str | `rcwl-development` | BigQuery project |
| `GCP_DATASET` | str | `powerbi_dashboard` | BigQuery dataset |
| `GOOGLE_APPLICATION_CREDENTIALS` | str | `./service-account.json` | GCP auth |
| `BIGQUERY_EVENTS_TABLE` | str | `growth_engine_events` | BQ table |
| `CMS_ADMIN_URL` | str | `https://admin.joinkliq.io` | CMS dashboard |
| `CLAIM_BASE_URL` | str | `http://localhost:8000/claim` | Claim page URL |
| `CLAIM_SECRET_KEY` | str | `change-me-in-production` | JWT signing |
| `SLACK_WEBHOOK_URL` | str | `""` | Error alerts |
| `SLACK_CHANNEL` | str | `#growth-engine` | Alert channel |
| `YOUTUBE_MAX_DAILY_UNITS` | int | `10000` | API quota |
| `SCRAPE_DELAY_SECONDS` | int | `2` | Rate limiting |
| `MAX_CONCURRENT_SCRAPES` | int | `5` | Parallelism |

## Conventions

### Naming
- Files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Dataclasses for output types (e.g., `GeneratedBio`, `BuiltEmail`, `EmailResult`)
- Pydantic models for API request/response (e.g., `ProspectResponse`, `ClaimRequest`)

### Imports
- Absolute imports from project root: `from app.db.models import Prospect`
- Lazy imports in Celery tasks to avoid circular dependencies: `from app.workers.scrape_tasks import discover_coaches_task`
- Jinja2 templates loaded via `FileSystemLoader` at module level

### Error Handling
- FastAPI: `HTTPException` for API errors
- Celery: `self.retry(exc=exc, countdown=N)` with `max_retries`
- Slack alerts on pipeline failures via `notify_pipeline_error()`
- BigQuery event logging for all major actions
- Custom exceptions: `ClaimError` for claim flow errors

### Design Tokens (Dashboard)
- Font: Sora / Inter
- Primary: `#1C3838` (Gable Green)
- Secondary: `#39938F` (Teal)
- Accent: `#FF9F88` (Tangerine)
- Background: `#FFFDF9` (Ivory)
- Borders: `#F3F4F6`

### CMS Constants
- STATUS_INACTIVE = 1 (Draft)
- STATUS_ACTIVE = 2 (Live)
- USER_TYPE_COACH_ADMIN = 3
- CURRENCY_USD = 2
- SUPER_ADMIN_ID = 1

### Beat Schedule
- `daily-discovery`: 6:00 AM UTC daily — YouTube discovery with 5 fitness queries
- `outreach-processor`: Every 30 minutes — process pending outreach emails

### Email Steps
- Step 1: "Store ready" (immediate) → Step 2: "Reminder 1" (+3 days) → Step 3: "Reminder 2" (+7 days) → Step 4: "Claimed confirmation" (immediate on claim)
