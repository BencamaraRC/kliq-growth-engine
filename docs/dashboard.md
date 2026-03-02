# Dashboard

> Streamlit multi-page dashboard with data layer, auth, and KLIQ design system.

## Overview

The dashboard is a Streamlit multi-page app that provides a visual interface for monitoring the Growth Engine pipeline. It shows KPIs, funnel metrics, prospect lists, campaign management, manual pipeline triggers, and store previews. It connects to the Growth Engine PostgreSQL database using synchronous SQLAlchemy.

## Files

| File | Purpose |
|------|---------|
| `dashboard/app.py` | Home page — KPIs, funnel, charts |
| `dashboard/theme.py` | KLIQ design system CSS, auth, sidebar nav, Plotly theme |
| `dashboard/data.py` | SQL queries returning DataFrames/dicts |
| `dashboard/auth_config.yaml` | User credentials for Streamlit authenticator |
| `dashboard/pages/profiles.py` | Prospect list with search/filter |
| `dashboard/pages/profile_detail.py` | Single prospect detail view |
| `dashboard/pages/pipeline.py` | Manual pipeline trigger interface |
| `dashboard/pages/campaigns.py` | Campaign management UI |
| `dashboard/pages/store_preview.py` | Visual store preview in iframe |

## Pages

### Home (`dashboard/app.py`)

**File:** `dashboard/app.py:1-145`

- **KPIs row:** Total prospects, stores created, emails sent, claims, claim rate
- **Funnel chart:** Bar chart of prospect counts by status (Plotly)
- **Platform breakdown:** Donut chart of prospects by platform
- **Daily activity:** Area chart (30 days) — discovered, stores_created, claimed
- **Top niches:** Horizontal bar chart of niche tag frequency
- **Status breakdown:** Table + email open rate + claim conversion metrics

### Profiles (`dashboard/pages/profiles.py`)

Searchable list of all prospects. Filter by name, platform, status, niche. Click through to detail page.

### Profile Detail (`dashboard/pages/profile_detail.py`)

Full prospect view: profile data, metrics, scraped content timeline, generated content preview, store preview link.

### Pipeline (`dashboard/pages/pipeline.py`)

Manual trigger interface with buttons:
- Trigger discovery (select platforms + queries)
- Scrape single coach (platform + ID)
- Run full pipeline for a prospect
- Task status polling

### Campaigns (`dashboard/pages/campaigns.py`)

Campaign management:
- Create new campaigns
- List active/inactive campaigns
- View email sends and engagement metrics

### Store Preview (`dashboard/pages/store_preview.py`)

**File:** `dashboard/pages/store_preview.py:1-132`

- Dropdown to select a prospect with generated content
- Renders full HTML mockup in an iframe
- Debug panel showing raw bio, SEO, colors, products, blogs data

## Data Layer

**File:** `dashboard/data.py`

Uses synchronous SQLAlchemy (Streamlit doesn't support async). Builds sync URL from the async `DATABASE_URL` by replacing `+asyncpg` with empty string.

### Key Functions

| Function | Returns | Description |
|----------|---------|-------------|
| `get_kpi_summary()` | dict | Top-level metrics (total, by status, rates) |
| `get_funnel_data()` | DataFrame | Prospect counts by status, ordered by pipeline stage |
| `get_platform_breakdown()` | DataFrame | Prospect counts by platform |
| `get_daily_activity(days)` | DataFrame | Daily discovered/stores/claims counts |
| `get_niche_distribution()` | DataFrame | Niche tag frequency across all prospects |

## Theme & Design System

**File:** `dashboard/theme.py:1-417`

### Colors

| Token | Hex | Usage |
|-------|-----|-------|
| Gable Green | `#1C3838` | Primary, headers |
| Teal | `#39938F` | Secondary, accents |
| Tangerine | `#FF9F88` | Highlights, CTAs |
| Ivory | `#FFFDF9` | Backgrounds |
| Borders | `#F3F4F6` | Dividers |

### Key Functions

| Function | Description |
|----------|-------------|
| `inject_kliq_theme()` | Injects CSS variables and custom styles |
| `sidebar_nav()` | Renders sidebar navigation with page links |
| `apply_plotly_theme(fig)` | Applies KLIQ colors/fonts to Plotly charts |

### Chart Colors

`CHART_COLORS = ["#1C3838", "#39938F", "#FF9F88", "#B8D4D2", "#FFD4C7", "#2D5A5A", "#5BB5B0"]`

### Auth

Uses `streamlit-authenticator` with YAML config. `inject_kliq_theme()` includes login flow with logout button in sidebar.

## Running

```bash
streamlit run dashboard/app.py
```

The dashboard reads from the same PostgreSQL database as the API. Make sure the database is running and migrated.
