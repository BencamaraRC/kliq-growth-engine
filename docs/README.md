# KLIQ Growth Engine Documentation

> Automated coach discovery, AI webstore generation, and outreach pipeline.

## Quickstart

```bash
# 1. Start infrastructure
docker compose up -d postgres redis

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Run database migrations
alembic upgrade head

# 4. Start the API server
uvicorn app.main:app --reload --port 8000

# 5. Start Celery worker + beat scheduler
celery -A app.workers.celery_app worker -l info -B

# 6. Start the dashboard
streamlit run dashboard/app.py
```

Copy `.env.example` to `.env` and fill in API keys before running.

## Project Structure

```
kliq-growth-engine/
├── app/                    # FastAPI + Celery application
│   ├── main.py             # App entrypoint, router mounting
│   ├── config.py           # Settings from .env (pydantic-settings)
│   ├── api/                # REST API endpoints
│   ├── db/                 # PostgreSQL models + session factories
│   ├── ai/                 # Claude-powered content generators
│   ├── scrapers/           # Platform adapters + discovery
│   ├── cms/                # KLIQ CMS MySQL integration
│   ├── workers/            # Celery tasks + beat schedule
│   ├── outreach/           # Email campaigns (Brevo)
│   ├── preview/            # Store preview renderer
│   ├── claim/              # Claim flow (HTML pages)
│   └── events/             # BigQuery analytics + Slack alerts
├── dashboard/              # Streamlit multi-page dashboard
├── migrations/             # Alembic database migrations
├── tests/                  # Pytest test suite
└── scripts/                # Utility scripts
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | System overview, data flow, infrastructure |
| [database.md](database.md) | Models, enums, relationships |
| [api-reference.md](api-reference.md) | All API endpoints |
| [scrapers.md](scrapers.md) | Platform adapters, discovery pipeline |
| [ai-pipeline.md](ai-pipeline.md) | AI content generation (bio, blogs, pricing, SEO) |
| [cms-integration.md](cms-integration.md) | Store builder, products, pages, auto-login |
| [outreach.md](outreach.md) | Email campaigns, templates, tracking, claim flow |
| [claim-flow.md](claim-flow.md) | Claim page, welcome page, token flow |
| [preview.md](preview.md) | Store preview renderer |
| [workers.md](workers.md) | Celery tasks, beat schedule, pipeline chain |
| [dashboard.md](dashboard.md) | Streamlit pages, data layer, auth, theme |
| [config.md](config.md) | Environment variables, settings reference |
| [LLM_CONTEXT.md](LLM_CONTEXT.md) | Machine-readable codebase context for AI assistants |

## Stack

- **API:** FastAPI + Uvicorn
- **Task Queue:** Celery + Redis
- **Databases:** PostgreSQL (Growth Engine) + MySQL (RCWL-CMS)
- **AI:** Anthropic Claude (Sonnet 4 / Opus 4)
- **Email:** Brevo (SendinBlue)
- **Scraping:** Playwright, YouTube Data API v3, Apify
- **Storage:** AWS S3
- **Analytics:** Google BigQuery
- **Dashboard:** Streamlit + Plotly
- **Notifications:** Slack webhooks

## Python Version

Requires Python 3.11+.
