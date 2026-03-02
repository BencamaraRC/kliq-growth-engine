# API Reference

> All REST API endpoints for the KLIQ Growth Engine.

## Overview

The Growth Engine exposes a FastAPI REST API on port 8000. Routers are mounted in `app/main.py`. All pipeline operations are async — they return a task ID for polling.

## Endpoints

### Health Check

#### `GET /health`

**File:** `app/main.py:33`

Returns server status.

**Response:**
```json
{ "status": "ok", "env": "development" }
```

---

### Prospects — `/api/prospects`

**File:** `app/api/prospects.py`

#### `GET /api/prospects/`

**File:** `app/api/prospects.py:35`

List all discovered prospects with optional filters.

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `status` | ProspectStatus | None | Filter by status |
| `platform` | Platform | None | Filter by platform |
| `limit` | int | 50 | Max results (max 200) |
| `offset` | int | 0 | Pagination offset |

**Response:** `ProspectListResponse`
```json
{
  "total": 150,
  "prospects": [
    {
      "id": 1,
      "name": "Coach Mike",
      "email": "mike@example.com",
      "status": "STORE_CREATED",
      "primary_platform": "YOUTUBE",
      "primary_platform_id": "UCxxx",
      "follower_count": 45000,
      "subscriber_count": 45000,
      "niche_tags": ["fitness", "strength"],
      "kliq_application_id": 42,
      "kliq_store_url": "https://coachmike.joinkliq.io"
    }
  ]
}
```

#### `GET /api/prospects/{prospect_id}`

**File:** `app/api/prospects.py:68`

Get a single prospect by ID. Returns 404 if not found.

---

### Campaigns — `/api/campaigns`

**File:** `app/api/campaigns.py`

#### `GET /api/campaigns/`

**File:** `app/api/campaigns.py:32`

List all campaigns, ordered by creation date descending.

**Response:** `list[CampaignResponse]`

#### `POST /api/campaigns/`

**File:** `app/api/campaigns.py:38`

Create a new campaign (status: DRAFT).

**Body:**
```json
{
  "name": "YouTube Fitness Q1",
  "platform_filter": "YOUTUBE",
  "niche_filter": ["fitness", "yoga"],
  "min_followers": 1000
}
```

#### `POST /api/campaigns/{campaign_id}/activate`

**File:** `app/api/campaigns.py:53`

Set campaign status to ACTIVE. Returns 404 if not found.

#### `POST /api/campaigns/{campaign_id}/pause`

**File:** `app/api/campaigns.py:66`

Set campaign status to PAUSED. Returns 404 if not found.

---

### Pipeline — `/api/pipeline`

**File:** `app/api/pipeline.py`

All pipeline endpoints return a task ID for async polling.

#### `POST /api/pipeline/discover`

**File:** `app/api/pipeline.py:35`

Trigger coach discovery across platforms. Queues a Celery `discover_coaches_task`.

**Body:**
```json
{
  "platforms": ["youtube"],
  "search_queries": ["fitness coach", "personal trainer", "wellness coach"],
  "max_per_platform": 50
}
```

**Response:**
```json
{ "task_id": "abc123-...", "status": "queued" }
```

#### `POST /api/pipeline/scrape`

**File:** `app/api/pipeline.py:52`

Scrape a single coach by platform and ID. Queues `scrape_single_coach_task`.

**Body:**
```json
{ "platform": "youtube", "platform_id": "UCxxx" }
```

#### `POST /api/pipeline/run/{prospect_id}`

**File:** `app/api/pipeline.py:64`

Run the full pipeline (AI generation + store creation) for a prospect. Queues `full_pipeline_task`.

#### `GET /api/pipeline/status/{task_id}`

**File:** `app/api/pipeline.py:73`

Check the status of an async task. Returns Celery task state (PENDING, STARTED, SUCCESS, FAILURE).

---

### Webhooks — `/api/webhooks`

**File:** `app/api/webhooks.py`

#### `POST /api/webhooks/claim`

**File:** `app/api/webhooks.py:31`

Handle store claim from coach. Validates token, activates store, sets password, sends confirmation.

**Body:**
```json
{ "token": "claim-jwt-token", "password": "newpassword123" }
```

**Response:**
```json
{
  "success": true,
  "message": "Store claimed successfully! Welcome to KLIQ.",
  "redirect_url": "https://admin.joinkliq.io/app/42"
}
```

#### `POST /api/webhooks/brevo`

**File:** `app/api/webhooks.py:74`

Handle email events from Brevo (opens, clicks, bounces, unsubscribes). Updates CampaignEvent records.

---

### Preview — `/preview`

**File:** `app/preview/router.py`

#### `GET /preview/{prospect_id}`

**File:** `app/preview/router.py:15`

Serve an animated HTML store preview. Public endpoint — no auth. Linked from outreach emails. Returns 404 if prospect or generated content not found.

---

### Claim Flow — `/claim`, `/welcome`

**File:** `app/claim/router.py`

#### `GET /claim?token={token}`

**File:** `app/claim/router.py:24`

Serve the claim page with password form. Shows error if token is invalid, or "already claimed" page if store is already active.

#### `POST /claim`

**File:** `app/claim/router.py:50`

Handle claim form submission. Validates password (min 8 chars, must match confirmation), activates store, redirects to `/welcome`.

**Form data:** `token`, `password`, `password_confirm`

#### `GET /welcome?token={token}`

**File:** `app/claim/router.py:117`

Serve the onboarding welcome page after claiming. Shows content counts and auto-login link to CMS dashboard. Redirects to `/claim` if not yet claimed.

## Response Models

| Model | File | Fields |
|-------|------|--------|
| `ProspectResponse` | `app/api/prospects.py:14` | id, name, email, status, primary_platform, primary_platform_id, follower_count, subscriber_count, niche_tags, kliq_application_id, kliq_store_url |
| `ProspectListResponse` | `app/api/prospects.py:30` | total, prospects |
| `CampaignCreate` | `app/api/campaigns.py:14` | name, platform_filter, niche_filter, min_followers |
| `CampaignResponse` | `app/api/campaigns.py:21` | id, name, status, platform_filter, niche_filter, min_followers |
| `DiscoverRequest` | `app/api/pipeline.py:9` | platforms, search_queries, max_per_platform |
| `ScrapeRequest` | `app/api/pipeline.py:17` | platform, platform_id |
| `PipelineStatusResponse` | `app/api/pipeline.py:30` | task_id, status |
| `ClaimRequest` | `app/api/webhooks.py:20` | token, password |
| `ClaimResponse` | `app/api/webhooks.py:25` | success, message, redirect_url |
