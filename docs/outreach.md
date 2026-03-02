# Outreach

> Email campaigns, templates, Brevo integration, and email event tracking.

## Overview

The outreach system manages a 4-step email lifecycle for each prospect. After a store is created, the system sends a "store ready" email, then two follow-up reminders if unclaimed. When a coach claims their store, a confirmation email is sent. Emails are sent via Brevo (SendinBlue) and tracking events (opens, clicks, bounces) are processed via webhooks.

## Files

| File | Purpose |
|------|---------|
| `app/outreach/campaign_manager.py` | Orchestrates 4-step email lifecycle |
| `app/outreach/email_builder.py` | Builds personalized HTML emails from templates |
| `app/outreach/brevo_client.py` | Brevo API client for sending emails |
| `app/outreach/claim_handler.py` | Token validation, store activation on claim |
| `app/outreach/tracking.py` | Processes Brevo webhook events |
| `app/outreach/templates/` | Jinja2 HTML email templates |

## Email Steps

| Step | Template | Subject | Timing |
|------|----------|---------|--------|
| 1 | `store_ready.html` | "{{ first_name }}, your KLIQ store is ready!" | Immediately after store creation |
| 2 | `reminder_1.html` | "{{ first_name }}, your store is waiting for you" | +3 days if unclaimed |
| 3 | `reminder_2.html` | "Last chance to claim {{ store_name }}" | +7 days from first email |
| 4 | `claimed_confirmation.html` | "Welcome to KLIQ, {{ first_name }}!" | Immediately on claim |

## Key Functions

### `process_outreach(session) → dict`

**File:** `app/outreach/campaign_manager.py:33`

Called every 30 minutes by Celery beat. Finds prospects needing emails and sends them.

1. Find prospects with status STORE_CREATED and no email sent → Send Step 1
2. Find prospects where Step 1 was sent 3+ days ago → Send Step 2
3. Find prospects where Step 2 was sent 4+ days after Step 1 → Send Step 3

Returns: `{ "initial_sends": int, "reminders_sent": int, "errors": int }`

### `send_claim_confirmation(session, prospect)`

**File:** `app/outreach/campaign_manager.py:81`

Sends the Step 4 confirmation email when a coach claims their store.

### `build_outreach_email(step, email, first_name, store_name, platform, claim_token, primary_color, ...) → BuiltEmail`

**File:** `app/outreach/email_builder.py:57`

Builds a personalized email for a specific step.

**Template context variables:**
| Variable | Description |
|----------|-------------|
| `first_name` | Coach's first name |
| `store_name` | Store display name |
| `platform` | Source platform name |
| `claim_url` | Full claim URL with token |
| `unsubscribe_url` | Unsubscribe link |
| `dashboard_url` | CMS dashboard link |
| `primary_color` | Brand hex color |
| `store_url` | Store preview URL |
| `tagline` | Coach tagline |
| `blog_count` | Number of blogs created |
| `product_count` | Number of products created |

**Returns `BuiltEmail`:** `to_email`, `to_name`, `subject`, `html_content`, `step`, `tags`

### `BrevoClient.send_email(to_email, to_name, subject, html_content, tags, params) → EmailResult`

**File:** `app/outreach/brevo_client.py:39`

Sends a transactional email via Brevo API. Includes List-Unsubscribe header.

**Returns `EmailResult`:** `success` (bool), `message_id` (str?), `error` (str?)

### `process_brevo_event(session, payload) → str`

**File:** `app/outreach/tracking.py:28`

Processes Brevo webhook events. Maps events to `EmailStatus`:

| Brevo Event | EmailStatus |
|-------------|-------------|
| delivered | SENT |
| opened | OPENED |
| click | CLICKED |
| hard_bounce | BOUNCED |
| soft_bounce | BOUNCED |
| unsubscribed | UNSUBSCRIBED |

On bounce or unsubscribe, marks the prospect as REJECTED to prevent further emails.

## Data Flow

```
Store Created → Step 1 email → (3 days) → Step 2 → (4 days) → Step 3
                     │                                              │
                     └──── Coach claims ──── Step 4 confirmation ───┘
                                │
                                ▼
                    Brevo Webhook → tracking.py → CampaignEvent update
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `BREVO_API_KEY` | — | Brevo API key |
| `BREVO_SENDER_EMAIL` | `growth@joinkliq.io` | From email address |
| `BREVO_SENDER_NAME` | `KLIQ Growth Team` | From display name |
| `CLAIM_BASE_URL` | `http://localhost:8000/claim` | Base URL for claim links |
| `CLAIM_SECRET_KEY` | `change-me-in-production` | JWT signing key for tokens |
