# Claim Flow

> Claim page, welcome page, and token-based store activation.

## Overview

The claim flow is the conversion mechanism. When a coach receives an outreach email, they click a link to see their pre-built store preview and claim it by setting a password. The flow: outreach email → preview page → claim page (set password) → welcome page (auto-login to CMS dashboard).

## Files

| File | Purpose |
|------|---------|
| `app/claim/router.py` | GET/POST /claim, GET /welcome routes |
| `app/claim/renderer.py` | HTML page renderers (claim, welcome, error, already-claimed) |
| `app/claim/queries.py` | Query helpers (get_prospect_by_token, get_content_counts, get_auto_login_token) |
| `app/outreach/claim_handler.py` | Token validation, store activation |

## Flow

```
Outreach Email
    │
    └── "Claim Your Store" button
            │
            ▼
    GET /claim?token=xxx
    (Renders claim page with password form)
            │
            ▼
    POST /claim
    (Validates password, activates store)
    Form fields: token, password, password_confirm
            │
            ├── Validation errors → Re-render claim page with errors
            ├── Already claimed → Render already-claimed page
            └── Success → Redirect 303 to /welcome?token=xxx
                    │
                    ▼
            GET /welcome?token=xxx
            (Shows content counts, auto-login link to CMS dashboard)
```

## Key Functions

### `validate_claim_token(growth_db, token) → Prospect`

**File:** `app/outreach/claim_handler.py:31`

Validates a claim token against the database.

**Raises `ClaimError`:**
- "Invalid claim token" — token not found
- "Store already claimed" — prospect status is CLAIMED
- "No store associated with this claim" — no `kliq_application_id`

### `activate_store(cms_db, growth_db, prospect, password) → dict`

**File:** `app/outreach/claim_handler.py:54`

Activates a claimed store:
1. Hash password with bcrypt
2. Generate auto-login token (30-minute expiry, 64-char hex)
3. Update CMS user: password, status=Active, email_verified=True, auto-login token
4. Update CMS application: status=Active
5. Update prospect: status=CLAIMED, claimed_at=now
6. Log BigQuery event, send Slack notification

**Returns:** `{ application_id, store_url, email, auto_login_token }`

### `get_prospect_by_token(session, token) → dict | None`

**File:** `app/claim/queries.py`

Query prospect by claim token. Returns dict with prospect fields or None.

### `get_content_counts(session, prospect_id) → dict`

**File:** `app/claim/queries.py`

Returns counts of generated content: `{ blogs: int, products: int }`.

### `get_auto_login_token(cms_db, prospect) → str | None`

**File:** `app/claim/queries.py`

Fetches the auto-login token from the CMS database for seamless dashboard access.

## Pages Rendered

| Page | Function | Description |
|------|----------|-------------|
| Claim Page | `render_claim_page(prospect, counts, errors)` | Password form + store summary |
| Welcome Page | `render_welcome_page(prospect, counts, auto_login_token)` | Onboarding + CMS link |
| Error Page | `render_error_page(title, message, cta_url, cta_text)` | Generic error |
| Already Claimed | `render_already_claimed_page(prospect)` | "Store already claimed" |

## Validation

Server-side validation in `POST /claim`:
- Token must be present
- Password minimum 8 characters
- Password and confirmation must match

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `CLAIM_BASE_URL` | `http://localhost:8000/claim` | Base URL for claim pages |
| `CLAIM_SECRET_KEY` | `change-me-in-production` | JWT signing key |
| `CMS_ADMIN_URL` | `https://admin.joinkliq.io` | CMS dashboard for redirect |
