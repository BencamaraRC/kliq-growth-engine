# Preview

> Store preview renderer — animated HTML pages showing a prospect's generated KLIQ store.

## Overview

The preview system renders a full HTML page showing what a prospect's KLIQ webstore would look like. It's a public endpoint (no auth) linked from outreach emails so coaches can see their store before claiming. The preview assembles data from the Growth Engine database (prospect + generated content) and renders it as a standalone HTML page with animations.

## Files

| File | Purpose |
|------|---------|
| `app/preview/router.py` | `GET /preview/{prospect_id}` route |
| `app/preview/renderer.py` | HTML rendering with inline CSS/JS |
| `app/preview/queries.py` | Query helpers for preview data |

## Key Functions

### `GET /preview/{prospect_id}`

**File:** `app/preview/router.py:15`

Serves the animated store preview. Public endpoint.

- Returns 404 if prospect not found
- Returns 404 if no generated content available yet
- Includes a "Claim Your Store" CTA button if the prospect has a claim token

### `get_prospect_by_id(session, prospect_id) → dict | None`

**File:** `app/preview/queries.py`

Loads prospect data for the preview.

### `get_generated_content(session, prospect_id) → dict | None`

**File:** `app/preview/queries.py`

Loads all generated content (bio, blogs, products, SEO, colors) for the preview. Returns structured dict.

### `render_store_preview(prospect, generated_content, claim_cta_url) → str`

**File:** `app/preview/renderer.py`

Renders the full HTML preview page. Includes:
- Profile header (name, tagline, avatar, banner)
- Brand colors applied throughout
- About section (long bio)
- Products/pricing cards
- Blog post previews
- SEO metadata in `<head>`
- Animated entrance effects (CSS transitions)
- "Claim Your Store" CTA button (if claim URL provided)

## Dashboard Preview

The Streamlit dashboard also has a store preview at `dashboard/pages/store_preview.py` that renders a similar preview in an iframe, with a debug panel showing raw bio, SEO, colors, products, and blogs data.
