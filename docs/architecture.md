# Architecture

> System overview, data flow, and infrastructure for the KLIQ Growth Engine.

## Overview

The Growth Engine automates the process of discovering fitness/wellness coaches on competitor platforms, generating AI-powered KLIQ webstores for them, and running email outreach to get them to claim their stores. It operates as a FastAPI application with Celery workers for async processing, backed by two databases (PostgreSQL for its own data, MySQL for the KLIQ CMS).

## System Diagram

```
                           ┌──────────────────────┐
                           │   Streamlit Dashboard │
                           │   (dashboard/app.py)  │
                           └───────────┬───────────┘
                                       │ SQL queries
                                       ▼
┌─────────────┐    REST    ┌──────────────────────┐     ┌──────────────┐
│  API Client │ ────────── │    FastAPI Server     │ ──▶ │  PostgreSQL  │
│  (browser)  │            │    (app/main.py)      │     │ Growth Engine│
└─────────────┘            └──────────┬───────────┘     └──────────────┘
                                      │ Celery
                                      ▼
                            ┌──────────────────────┐
                            │   Redis (Broker)     │
                            └──────────┬───────────┘
                                       │
                    ┌──────────────────┬┴───────────────────┐
                    ▼                  ▼                    ▼
          ┌──────────────┐   ┌──────────────┐    ┌──────────────────┐
          │ Scrape Tasks │   │  AI Tasks    │    │ Outreach Tasks   │
          │  (YouTube,   │   │ (Claude API) │    │ (Brevo emails)   │
          │  Skool, etc) │   │              │    │                  │
          └──────┬───────┘   └──────┬───────┘    └────────┬─────────┘
                 │                  │                      │
                 ▼                  ▼                      │
          ┌──────────────┐   ┌──────────────┐             │
          │ External APIs│   │ Populate     │             │
          │ (Google, etc)│   │ Tasks        │             │
          └──────────────┘   │ (Store Build)│             │
                             └──────┬───────┘             │
                                    │                     │
                                    ▼                     ▼
                            ┌──────────────┐    ┌──────────────────┐
                            │   MySQL      │    │   Brevo API      │
                            │  RCWL-CMS    │    │  (email sending) │
                            └──────────────┘    └──────────────────┘
                                    │
                    ┌───────────────┴──────────────┐
                    ▼                              ▼
             ┌───────────┐                 ┌──────────────┐
             │  AWS S3   │                 │  BigQuery    │
             │  (media)  │                 │  (analytics) │
             └───────────┘                 └──────────────┘
```

## Pipeline Stages

A prospect moves through these statuses in order:

```
DISCOVERED → SCRAPED → CONTENT_GENERATED → STORE_CREATED → EMAIL_SENT → CLAIMED
                                                                    └──→ REJECTED
```

| Stage | What Happens | Key Module |
|-------|-------------|------------|
| Discovery | Find coaches on YouTube/Skool/Patreon via search | `app/scrapers/` |
| Scraping | Scrape profiles, content, and pricing | `app/scrapers/` |
| AI Generation | Generate bio, blogs, pricing, SEO, colors | `app/ai/` |
| Store Creation | Build a complete KLIQ webstore in the CMS | `app/cms/` |
| Outreach | 4-step email sequence via Brevo | `app/outreach/` |
| Claim | Coach claims store, sets password, goes active | `app/claim/` |

## Key Patterns

### Dual Database

The system writes to two databases:
- **PostgreSQL** (`app/db/`) — Growth Engine's own data (prospects, scraped content, generated content, campaigns)
- **MySQL** (`app/cms/`) — The RCWL-CMS database (applications, users, products, pages). The Growth Engine writes directly to CMS tables to create stores, replicating the Laravel `ApplicationController::store` flow.

### Async Bridge

Celery workers run in sync context but the codebase is async-first. Each task uses `_run_async()` to bridge:
```python
def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()
```

### Task Chaining

The full pipeline uses Celery chains:
```python
chain(generate_content_task.si(prospect_id=id), create_store_task.si(prospect_id=id))
```

### Buffered Analytics

BigQuery events are buffered in memory (50 events or 30 seconds) to reduce API calls. The `BigQueryLogger` is a thread-safe singleton.

## Infrastructure

| Service | Technology | Config Key |
|---------|-----------|------------|
| API Server | FastAPI + Uvicorn | `APP_PORT` (8000) |
| Task Queue | Celery + Redis | `REDIS_URL` |
| Growth DB | PostgreSQL (asyncpg) | `DATABASE_URL` |
| CMS DB | MySQL (aiomysql) | `CMS_DATABASE_URL` |
| AI | Anthropic Claude | `ANTHROPIC_API_KEY` |
| Email | Brevo | `BREVO_API_KEY` |
| Video API | YouTube Data API v3 | `YOUTUBE_API_KEY` |
| Storage | AWS S3 | `AWS_ACCESS_KEY_ID` |
| Analytics | Google BigQuery | `GCP_PROJECT_ID` |
| Scraping | Apify (Skool) | `APIFY_API_TOKEN` |
| Alerts | Slack webhooks | `SLACK_WEBHOOK_URL` |
| Dashboard | Streamlit | N/A (runs separately) |

## Files

| File | Purpose |
|------|---------|
| `app/main.py` | FastAPI app init, router mounting, health check |
| `app/config.py` | Pydantic settings from `.env` |
| `app/db/session.py` | Async engine/session factories for both databases |
| `docker-compose.yml` | PostgreSQL + Redis dev stack |
| `alembic.ini` | Migration configuration |
| `pyproject.toml` | Dependencies and build config |
