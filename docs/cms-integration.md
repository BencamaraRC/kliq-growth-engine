# CMS Integration

> Store builder, product creation, content pages, and media uploads.

## Overview

The CMS integration layer writes directly to the RCWL-CMS MySQL database to create complete KLIQ webstores. It replicates the Laravel `ApplicationController::store` bootstrap flow: creating the application, settings, colors, user account, roles, permissions, email templates, products, and pages. All records start as Draft (status_id=1) and go Active (status_id=2) when the coach claims the store.

## Files

| File | Purpose |
|------|---------|
| `app/cms/models.py` | SQLAlchemy models mirroring CMS MySQL tables |
| `app/cms/store_builder.py` | Create complete webstore (Application + full bootstrap) |
| `app/cms/products.py` | Create product tiers from pricing analysis |
| `app/cms/content.py` | Create About pages and blog pages |
| `app/cms/media.py` | Upload profile/banner images to S3 |

## Key Functions

### `build_store(session, name, email, first_name, last_name, ...) → StoreCreationResult`

**File:** `app/cms/store_builder.py:72`

Creates a complete KLIQ webstore by writing to 15+ CMS tables. Replicates `ApplicationController::store` (lines 67-196 in Laravel).

**Creation order:**
1. `Application` — Store instance with GUID
2. `ApplicationSetting` — Name, SEO, support email, brand config
3. `ApplicationFeatureSetup` — Feature toggles
4. `ApplicationColor` — Brand color scheme (6 colors)
5. `AudioSetting` — Default audio preferences
6. `Role` — "Coach Admin" role for the store
7. `ApplicationRole` — Bind role to application
8. `UserApplication` — Link super admin to store
9. `CMSUser` — Coach account with temp password
10. `UserDetail` — Profile metadata
11. `UserRole` — Assign Coach Admin role
12. `PermissionModule` + `PermissionReference` + `PermissionGroup` — Full permission set
13. `EmailTemplate` + `EmailTemplateType` — Transactional email templates
14. `ReferralPoint` — Default referral config

**Returns `StoreCreationResult`:**
| Field | Type | Description |
|-------|------|-------------|
| `application_id` | int | CMS application ID |
| `guid` | str | Application GUID |
| `user_id` | int | Coach user ID |
| `role_id` | int | Coach Admin role ID |
| `temp_password` | str | Temporary password (replaced on claim) |
| `store_url` | str | Public store URL |

**Constants:**
| Constant | Value | Meaning |
|----------|-------|---------|
| `STATUS_INACTIVE` | 1 | Draft — not visible |
| `STATUS_ACTIVE` | 2 | Live — visible to public |
| `USER_TYPE_COACH_ADMIN` | 3 | Coach admin user type |
| `CURRENCY_USD` | 2 | USD currency ID |
| `SUPER_ADMIN_ID` | 1 | Super admin user ID |

### `create_products(session, application_id, products, currency_id=2) → list[int]`

**File:** `app/cms/products.py:17`

Creates draft products in the CMS from AI-suggested pricing.

- Products created with status_id=1 (Draft), no Stripe connection
- Currency mapping: GBP=1, USD=2, EUR=3
- One-time products get interval="one_time"
- Returns list of created product IDs

### `create_about_page(session, application_id, long_bio, tagline, profile_image_url) → int`

**File:** `app/cms/content.py:18`

Creates an About page (page_type_id=1) with the AI-generated long bio.

### `create_blog_pages(session, application_id, blogs) → list[int]`

**File:** `app/cms/content.py:55`

Creates blog post pages (page_type_id=2) from AI-generated blogs. Returns list of created page IDs.

### `upload_image_from_url(image_url, s3_key, content_type) → str | None`

**File:** `app/cms/media.py:24`

Downloads an image from a URL and uploads it to S3. Returns the S3 URL or None on failure.

### `upload_store_images(application_id, profile_image_url, banner_image_url) → dict`

**File:** `app/cms/media.py`

Uploads both profile and banner images for a store. Returns dict with S3 URLs.

## Data Flow

```
AI Generated Content (Growth DB)
    │
    ├── Bio → create_about_page()
    ├── Blogs → create_blog_pages()
    ├── Pricing → create_products()
    ├── SEO → build_store() settings
    └── Colors → build_store() colors
          │
          ▼
    CMS MySQL Database
    (status_id=1, Draft)
          │
          ▼ (on claim)
    CMS MySQL Database
    (status_id=2, Active)
```

## Configuration

| Variable | Description |
|----------|-------------|
| `CMS_DATABASE_URL` | MySQL connection string for RCWL-CMS |
| `AWS_ACCESS_KEY_ID` | S3 access key for media uploads |
| `AWS_SECRET_ACCESS_KEY` | S3 secret key |
| `AWS_S3_BUCKET` | S3 bucket name (default: `dev-rcwl-assets`) |
| `AWS_S3_REGION` | S3 region (default: `eu-west-1`) |
| `CMS_ADMIN_URL` | CMS dashboard URL for redirect links |
