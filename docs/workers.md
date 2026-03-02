# Workers

> Celery tasks, beat schedule, and pipeline chain orchestration.

## Overview

The Growth Engine uses Celery with Redis as broker/backend for async task processing. Tasks handle scraping, AI generation, store creation, and email sending. The beat scheduler runs daily discovery and outreach processing every 30 minutes.

## Files

| File | Purpose |
|------|---------|
| `app/workers/celery_app.py` | Celery config, broker/backend, beat schedule |
| `app/workers/scrape_tasks.py` | Discovery and single-coach scraping |
| `app/workers/ai_tasks.py` | AI content generation orchestration |
| `app/workers/pipeline_task.py` | Full pipeline chain (AI → store → outreach) |
| `app/workers/populate_tasks.py` | CMS store creation |
| `app/workers/outreach_tasks.py` | Email sending |

## Celery Configuration

**File:** `app/workers/celery_app.py:8`

| Setting | Value |
|---------|-------|
| Broker | Redis (`REDIS_URL`) |
| Backend | Redis (`REDIS_URL`) |
| Serializer | JSON |
| Task ack | Late (after completion) |
| Prefetch | 1 (one task at a time) |
| Soft time limit | 300s (5 min) |
| Hard time limit | 600s (10 min) |
| Timezone | UTC |

## Beat Schedule (Periodic Tasks)

**File:** `app/workers/celery_app.py:36`

| Name | Schedule | Task | Config |
|------|----------|------|--------|
| `daily-discovery` | 6:00 AM UTC daily | `discover_coaches_task` | platforms=["youtube"], queries=["fitness coach", "personal trainer", "wellness coach", "yoga instructor", "nutrition coach"], max=50 |
| `outreach-processor` | Every 30 minutes | `process_outreach_queue` | (no args) |

## Tasks

### `discover_coaches_task(platforms, search_queries, max_per_platform)`

**File:** `app/workers/scrape_tasks.py:20`

Discovers coaches across platforms and stores in database. Uses `DiscoveryOrchestrator` with available adapters. Deduplicates against existing prospects by platform + platform_id.

**Args:**
| Param | Type | Default |
|-------|------|---------|
| `platforms` | list[str] | ["youtube"] |
| `search_queries` | list[str] | ["fitness coach", "personal trainer", "wellness coach"] |
| `max_per_platform` | int | 50 |

### `scrape_single_coach_task(platform, platform_id)`

**File:** `app/workers/scrape_tasks.py:116`

Scrapes a single coach by platform and ID. Creates or updates the prospect record, then scrapes profile, content, and pricing. Updates status to SCRAPED.

### `generate_content_task(prospect_id)`

**File:** `app/workers/ai_tasks.py:41`

Generates all AI content for a prospect. Orchestrates in order:

1. **Bio** — tagline, short/long bio, specialties, coaching style
2. **Blogs** — up to 5 blog posts from top-viewed video transcripts
3. **Pricing** — product recommendations from competitor tiers
4. **SEO** — titles, descriptions, keywords, slug
5. **Colors** — brand colors from profile image

Each result stored as a `GeneratedContent` row. Updates prospect status to CONTENT_GENERATED. Retries up to 2 times (60s countdown). Sends Slack alert on failure.

### `create_store_task(prospect_id)`

**File:** `app/workers/populate_tasks.py:41`

Creates a KLIQ webstore in the CMS MySQL database:

1. Load prospect + generated content from Growth DB
2. Parse bio, SEO, colors, products, blogs from generated content
3. `build_store()` — Application, settings, colors, user, roles, permissions
4. `create_products()` — Draft products from pricing analysis
5. `create_about_page()` + `create_blog_pages()` — Content pages
6. `upload_store_images()` — Profile/banner to S3
7. Update prospect: status=STORE_CREATED, kliq_application_id, kliq_store_url, claim_token

Retries up to 1 time (120s countdown). Sends Slack alert on failure.

### `full_pipeline_task(prospect_id)`

**File:** `app/workers/pipeline_task.py:15`

Chains AI generation and store creation using Celery `chain()`:

```python
chain(
    generate_content_task.si(prospect_id=prospect_id),
    create_store_task.si(prospect_id=prospect_id),
)
```

Scraping must be done before calling this task.

### `send_outreach_email_task(prospect_id, step, campaign_id)`

**File:** `app/workers/outreach_tasks.py:31`

Sends a single outreach email for a specific step (1-4).

### `process_outreach_queue()`

**File:** `app/workers/outreach_tasks.py:89`

Finds prospects due for emails and sends them. Called every 30 minutes by beat scheduler. Delegates to `process_outreach()` in campaign_manager.

## Pipeline Chain

```
discover_coaches_task
    │
    ▼ (for each prospect)
scrape_single_coach_task
    │
    ▼
full_pipeline_task
    │
    ├── generate_content_task
    │       │
    │       ▼
    └── create_store_task
            │
            ▼
    process_outreach_queue (beat, every 30 min)
        │
        └── send_outreach_email_task (step 1, 2, 3)
```

## Running

```bash
# Worker + beat scheduler in one process
celery -A app.workers.celery_app worker -l info -B

# Or separately
celery -A app.workers.celery_app worker -l info
celery -A app.workers.celery_app beat -l info
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_URL` | `redis://localhost:6379/0` | Celery broker and backend |
