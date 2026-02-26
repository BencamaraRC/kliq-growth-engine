# KLIQ Growth Engine

Automated coach discovery, webstore generation, and outreach pipeline for [KLIQ](https://joinkliq.io).

The Growth Engine discovers fitness/wellness coaches on competitor platforms (YouTube, Skool, Patreon, websites), uses AI to generate personalized store content, auto-builds KLIQ webstores, and runs email outreach campaigns — all as a continuous automated loop.

```
Discover → Scrape → AI Generate → Build Store → Email Outreach → Coach Claims Store
```

## Problem

KLIQ has 91.2% coach churn at 90 days because coaches never activate their stores. The Growth Engine solves this by **pre-building webstores** for coaches and emailing them to claim their ready-made store.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                   KLIQ GROWTH ENGINE                     │
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌───────────┐  │
│  │  FastAPI      │    │  Celery       │    │ Streamlit  │  │
│  │  (REST API +  │    │  Workers      │    │ Dashboard  │  │
│  │   webhooks)   │    │  (async jobs) │    │            │  │
│  └──────┬───────┘    └──────┬───────┘    └───────────┘  │
│         └───────────┬───────┘                           │
│                     │                                    │
│  ┌──────────────────┴────────────────────────────────┐  │
│  │              PIPELINE LAYERS                       │  │
│  │                                                    │  │
│  │  1. SCRAPERS        youtube | skool | patreon |    │  │
│  │     (Adapters)      website | tiktok | instagram   │  │
│  │                                                    │  │
│  │  2. AI PIPELINE     bio | blog | pricing | seo |   │  │
│  │     (Claude API)    color extraction               │  │
│  │                                                    │  │
│  │  3. CMS POPULATOR   store builder | products |     │  │
│  │     (Direct MySQL)  pages | media (S3)             │  │
│  │                                                    │  │
│  │  4. OUTREACH        brevo emails | 4-step campaign │  │
│  │     (Brevo)         claim flow | tracking          │  │
│  └────────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────┐  ┌────────────────────┐ │
│  │  PostgreSQL   │  │  Redis    │  │  Claude API        │ │
│  │  (Growth DB)  │  │  (Queue)  │  │  (Content Gen)     │ │
│  └──────────────┘  └──────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Project Structure

```
kliq-growth-engine/
├── app/
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment configuration
│   ├── scrapers/               # Platform adapters (Strategy pattern)
│   │   ├── base.py             # PlatformAdapter ABC + dataclasses
│   │   ├── youtube.py          # YouTube Data API v3 + transcripts
│   │   ├── skool.py            # Apify + Playwright fallback
│   │   ├── patreon.py          # Patreon API v2 + Playwright fallback
│   │   ├── website.py          # Playwright + BeautifulSoup
│   │   ├── discovery.py        # Cross-platform orchestrator + dedup
│   │   └── color_extractor.py  # Brand color extraction
│   ├── ai/                     # AI content generation (Claude API)
│   │   ├── client.py           # Claude API wrapper with retry
│   │   ├── bio_generator.py    # Profile → coach bio
│   │   ├── blog_generator.py   # Video transcripts → blog posts
│   │   ├── pricing_analyzer.py # Competitor pricing → product tiers
│   │   ├── seo_generator.py    # SEO metadata generation
│   │   └── prompts/            # Jinja2 prompt templates
│   ├── cms/                    # KLIQ CMS population (direct MySQL)
│   │   ├── store_builder.py    # Full store creation
│   │   ├── models.py           # SQLAlchemy models (CMS schema)
│   │   ├── products.py         # Product/subscription creation
│   │   ├── content.py          # Pages (about, blog)
│   │   └── media.py            # S3 image uploads
│   ├── outreach/               # Email outreach (Brevo)
│   │   ├── campaign_manager.py # 4-step campaign lifecycle
│   │   ├── email_builder.py    # Personalized email construction
│   │   ├── brevo_client.py     # Brevo API client
│   │   ├── claim_handler.py    # Store claim/activation flow
│   │   ├── tracking.py         # Open/click/bounce tracking
│   │   └── templates/          # HTML email templates
│   ├── events/                 # Monitoring & alerting
│   │   ├── bigquery.py         # Buffered event logging
│   │   └── slack.py            # Slack webhook alerts
│   ├── workers/                # Celery tasks
│   │   ├── celery_app.py       # Celery configuration
│   │   ├── scrape_tasks.py     # Discovery & scraping jobs
│   │   ├── ai_tasks.py         # AI generation jobs
│   │   ├── populate_tasks.py   # CMS population jobs
│   │   ├── outreach_tasks.py   # Email sending jobs
│   │   └── pipeline_task.py    # Full pipeline orchestration
│   ├── api/                    # FastAPI routes
│   │   ├── prospects.py        # Prospect CRUD
│   │   ├── campaigns.py        # Campaign management
│   │   ├── pipeline.py         # Pipeline triggers
│   │   └── webhooks.py         # Claim + Brevo webhooks
│   └── db/                     # Growth Engine database
│       ├── models.py           # SQLAlchemy models (PostgreSQL)
│       └── session.py          # Dual DB session management
├── dashboard/                  # Streamlit monitoring dashboard
│   ├── app.py                  # Home — KPIs and funnel
│   ├── data.py                 # Shared data access layer
│   └── pages/
│       ├── growth_engine.py    # Pipeline monitor
│       ├── competitor_intel.py # Discovered coaches browser
│       └── campaign_manager.py # Outreach performance
├── tests/                      # 107 tests
├── docker-compose.yml          # Local dev stack
├── Dockerfile
├── alembic.ini                 # DB migrations
└── pyproject.toml
```

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker (optional, for local services)

### Setup

```bash
# Clone
git clone https://github.com/BencamaraRC/kliq-growth-engine.git
cd kliq-growth-engine

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Install Playwright browsers
playwright install chromium

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start local services
docker compose up -d postgres redis

# Run database migrations
alembic upgrade head
```

### Run

```bash
# API server
uvicorn app.main:app --reload --port 8000

# Celery worker (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Dashboard (separate terminal)
streamlit run dashboard/app.py
```

### Run Tests

```bash
pytest tests/ -v
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/prospects/` | List prospects (filterable) |
| `GET` | `/api/prospects/{id}` | Get prospect detail |
| `POST` | `/api/pipeline/discover` | Trigger multi-platform discovery |
| `POST` | `/api/pipeline/scrape` | Scrape a single coach |
| `POST` | `/api/pipeline/run/{id}` | Run full pipeline for a prospect |
| `GET` | `/api/pipeline/status/{task_id}` | Check async task status |
| `GET` | `/api/campaigns/` | List campaigns |
| `POST` | `/api/campaigns/` | Create campaign |
| `POST` | `/api/campaigns/{id}/activate` | Activate campaign |
| `POST` | `/api/campaigns/{id}/pause` | Pause campaign |
| `POST` | `/api/webhooks/claim` | Coach claims store |
| `POST` | `/api/webhooks/brevo` | Brevo email events |

## Platform Adapters

Every platform implements the same `PlatformAdapter` interface. Adding a new platform = implement the interface in a new file.

| Platform | Method | Key Data |
|----------|--------|----------|
| YouTube | Data API v3 + youtube-transcript-api | Channel info, videos, transcripts, thumbnails |
| Skool | Apify + Playwright fallback | Community name, description, pricing, posts |
| Patreon | API v2 + Playwright fallback | Profile, tiers, public posts |
| Website | Playwright + BeautifulSoup | Blogs, images, brand colors, social links |
| TikTok | Stub (future) | — |
| Instagram | Stub (future) | — |

## Email Campaign Flow

4-step automated sequence:

1. **"Your store is ready"** — sent immediately after store creation
2. **Reminder 1** — +3 days if unclaimed
3. **Reminder 2** — +7 days if unclaimed
4. **Claimed confirmation** — sent on claim

Each email is personalized with the coach's name, branding, platform, and a preview of their store.

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.11+ |
| API | FastAPI |
| Task Queue | Celery + Redis |
| Growth DB | PostgreSQL (async, SQLAlchemy 2.0) |
| CMS DB | MySQL (RCWL-CMS, direct writes) |
| AI | Claude API (Anthropic) |
| Scraping | Playwright + BeautifulSoup |
| Email | Brevo (SendinBlue) |
| Storage | AWS S3 |
| Analytics | BigQuery |
| Dashboard | Streamlit + Plotly |
| Alerts | Slack webhooks |

## Environment Variables

See [`.env.example`](.env.example) for the full list. Key variables:

- `DATABASE_URL` — PostgreSQL connection (Growth Engine DB)
- `CMS_DATABASE_URL` — MySQL connection (RCWL-CMS)
- `ANTHROPIC_API_KEY` — Claude API for content generation
- `YOUTUBE_API_KEY` — YouTube Data API v3
- `BREVO_API_KEY` — Email outreach
- `SLACK_WEBHOOK_URL` — Pipeline alerts
