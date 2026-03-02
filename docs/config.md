# Configuration

> All environment variables and settings for the KLIQ Growth Engine.

## Overview

Configuration is managed via `pydantic-settings` in `app/config.py`. All settings are loaded from environment variables or a `.env` file. Copy `.env.example` to `.env` and fill in API keys before running.

## Files

| File | Purpose |
|------|---------|
| `app/config.py` | `Settings` class (pydantic-settings) |
| `.env.example` | Template with all variables |
| `.env` | Local secrets (gitignored) |

## Settings Reference

**File:** `app/config.py:4-68`

### Application

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `APP_ENV` | str | `development` | Environment (development/production) |
| `APP_DEBUG` | bool | `True` | FastAPI debug mode, SQLAlchemy echo |
| `APP_PORT` | int | `8000` | Uvicorn server port |
| `APP_BASE_URL` | str | `http://localhost:8000` | Base URL for generated links |

### Databases

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | `postgresql+asyncpg://...localhost:5433/kliq_growth_engine` | Growth Engine PostgreSQL (async) |
| `CMS_DATABASE_URL` | str | `mysql+aiomysql://root:password@localhost:3306/rcwlcmsweb2022` | RCWL-CMS MySQL (async, direct writes) |
| `REDIS_URL` | str | `redis://localhost:6379/0` | Celery broker/backend, cache |

### AI

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `ANTHROPIC_API_KEY` | str | `""` | Claude API key |

### Scraping

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `YOUTUBE_API_KEY` | str | `""` | Google YouTube Data API v3 key |
| `APIFY_API_TOKEN` | str | `""` | Apify API token (Skool scraping) |
| `PATREON_CLIENT_ID` | str | `""` | Patreon OAuth client ID |
| `PATREON_CLIENT_SECRET` | str | `""` | Patreon OAuth client secret |

### Email (Brevo)

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `BREVO_API_KEY` | str | `""` | Brevo (SendinBlue) API key |
| `BREVO_SENDER_EMAIL` | str | `growth@joinkliq.io` | From email address |
| `BREVO_SENDER_NAME` | str | `KLIQ Growth Team` | From display name |

### AWS S3

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AWS_ACCESS_KEY_ID` | str | `""` | S3 access key |
| `AWS_SECRET_ACCESS_KEY` | str | `""` | S3 secret key |
| `AWS_S3_BUCKET` | str | `dev-rcwl-assets` | S3 bucket name |
| `AWS_S3_REGION` | str | `eu-west-1` | S3 region |

### Google Cloud

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `GCP_PROJECT_ID` | str | `rcwl-development` | BigQuery project |
| `GCP_DATASET` | str | `powerbi_dashboard` | BigQuery dataset |
| `GOOGLE_APPLICATION_CREDENTIALS` | str | `./service-account.json` | Path to GCP service account JSON |
| `BIGQUERY_EVENTS_TABLE` | str | `growth_engine_events` | BigQuery events table name |

### Claim Flow

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `CMS_ADMIN_URL` | str | `https://admin.joinkliq.io` | CMS dashboard URL for redirects |
| `CLAIM_BASE_URL` | str | `http://localhost:8000/claim` | Base URL for claim pages |
| `CLAIM_SECRET_KEY` | str | `change-me-in-production` | JWT signing key for claim tokens |

### Slack

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SLACK_WEBHOOK_URL` | str | `""` | Incoming webhook URL |
| `SLACK_CHANNEL` | str | `#growth-engine` | Alert channel |

### Rate Limits

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `YOUTUBE_MAX_DAILY_UNITS` | int | `10000` | YouTube API daily quota |
| `SCRAPE_DELAY_SECONDS` | int | `2` | Delay between scrape requests |
| `MAX_CONCURRENT_SCRAPES` | int | `5` | Maximum parallel scrapes |

## Usage

Settings are accessed via the singleton:

```python
from app.config import settings

settings.database_url
settings.anthropic_api_key
settings.brevo_api_key
```

The `.env` file is loaded automatically by pydantic-settings:

```python
model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```
