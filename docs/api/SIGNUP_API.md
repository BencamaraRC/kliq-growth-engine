# Signup API — CMS Integration

## Overview

When a coach clicks their claim link, the Growth Engine redirects them to the CMS signup page with their prospect ID. The CMS then calls the Growth Engine API to fetch the coach's details and pre-fill the signup form.

## Flow

```
1. Coach clicks claim link:
   GET https://kliq-growth-api-512447837673.europe-west1.run.app/claim?token=xxx

2. Growth Engine validates token and redirects:
   302 → {CMS_ADMIN_URL}/signup?id={prospect_id}

3. CMS reads `id` from query param and calls:
   GET https://kliq-growth-api-512447837673.europe-west1.run.app/api/prospects/{id}/signup

4. CMS pre-fills the signup form with the returned data
```

## API Endpoint

### `GET /api/prospects/{id}/signup`

Returns prospect details for the CMS signup page.

**Base URL:** `https://kliq-growth-api-512447837673.europe-west1.run.app`

**Example Request:**
```
GET /api/prospects/1162/signup
```

**Example Response:**
```json
{
    "id": 1162,
    "name": "Radhika Evaluator",
    "email": "Radhikamb@gmail.com",
    "coach_type": "ICF Certified Coach",
    "profile_image": null,
    "banner_image": null
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Prospect ID |
| `name` | string | Coach's display name |
| `email` | string \| null | Coach's email address |
| `coach_type` | string | Derived from niche tags or platform (e.g. "ICF Certified Coach", "fitness", "yoga") |
| `profile_image` | string \| null | URL to coach's profile image |
| `banner_image` | string \| null | URL to coach's banner/hero image |

### Error Responses

**404 — Prospect not found:**
```json
{
    "detail": "Prospect not found"
}
```

### `coach_type` Logic

The `coach_type` field is derived in this order:
1. First item from `niche_tags` array (e.g. "fitness", "ICF Certified Coach")
2. If no niche tags, falls back to `{platform} coach` (e.g. "youtube coach")

## CORS

The API allows all origins (`*`), so the CMS can call it directly from the frontend or backend.

## Implementation Reference

- **Endpoint:** `app/api/prospects.py` → `get_signup_details()`
- **Claim redirect:** `app/claim/router.py` → `claim_page()`
