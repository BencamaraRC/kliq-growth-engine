# AI Pipeline

> AI-powered content generation using Claude for bios, blogs, pricing analysis, and SEO.

## Overview

The AI pipeline takes scraped profile data and generates everything needed for a KLIQ webstore: coach bio, blog posts from video transcripts, product/pricing recommendations, SEO metadata, and brand colors. All generators use the Anthropic Claude API via a shared client with retry logic.

## Files

| File | Purpose |
|------|---------|
| `app/ai/client.py` | Claude API wrapper with retries, JSON parsing, token tracking |
| `app/ai/bio_generator.py` | Generate tagline, bio, specialties, coaching style |
| `app/ai/blog_generator.py` | Generate blog posts from video transcripts |
| `app/ai/pricing_analyzer.py` | Analyze competitor pricing, suggest KLIQ products |
| `app/ai/seo_generator.py` | Generate SEO titles, descriptions, keywords, slug |
| `app/ai/prompts/` | Jinja2 prompt templates (`.j2` files) |

## AIClient

**File:** `app/ai/client.py:31`

Wrapper around the Anthropic SDK.

| Config | Value |
|--------|-------|
| Models | Sonnet 4 (fast, default), Opus 4 (complex tasks) |
| Retry | 3 attempts, exponential backoff (1s base, 30s max) |
| Handles | RateLimitError, 5xx server errors |

### `generate(prompt, system, model, max_tokens, temperature) → str`
**File:** `app/ai/client.py:39`

Text completion with retry logic. Default: Sonnet, 4096 tokens, temp 0.7.

### `generate_json(prompt, system, model, max_tokens, temperature) → dict`
**File:** `app/ai/client.py:97`

Structured JSON output. Appends JSON instruction to prompt, strips markdown fences, retries once on parse failure with a correction prompt. Default temp: 0.4.

### `usage_summary` → dict
**File:** `app/ai/client.py:166`

Cumulative token counts: `input_tokens`, `output_tokens`, `total_tokens`.

## Generators

### Bio Generator

**File:** `app/ai/bio_generator.py`

#### `generate_bio(client, name, platform, bio, niche_tags, follower_count, content_count, content_titles) → GeneratedBio`
**File:** `app/ai/bio_generator.py:30`

Generates a polished coach bio for their KLIQ store About page.

**Input:** Profile data + content titles for context.

**Output — `GeneratedBio`:**
| Field | Type | Description |
|-------|------|-------------|
| `tagline` | str | Short catchphrase |
| `short_bio` | str | 1-2 sentence bio |
| `long_bio` | str | Full About page content |
| `specialties` | list[str] | Areas of expertise |
| `coaching_style` | str | Coaching approach description |

**System prompt:** "You are a professional copywriter for KLIQ, a fitness/wellness creator platform."

### Blog Generator

**File:** `app/ai/blog_generator.py`

#### `generate_blog(client, coach_name, title, transcript, description, view_count, video_url) → GeneratedBlog | None`
**File:** `app/ai/blog_generator.py:35`

Generates a single blog post from a video transcript. Returns None if transcript is under 200 characters.

- Transcript truncated at 12,000 chars
- System prompt: "You are a content writer for KLIQ..."

#### `generate_blogs_batch(client, coach_name, videos, max_blogs=5) → list[GeneratedBlog]`
**File:** `app/ai/blog_generator.py:100`

Generates up to 5 blogs from the highest-view videos with usable transcripts.

**Output — `GeneratedBlog`:**
| Field | Type | Description |
|-------|------|-------------|
| `blog_title` | str | Blog post title |
| `excerpt` | str | Short summary |
| `body_html` | str | Full HTML body |
| `tags` | list[str] | Content tags |
| `seo_title` | str | Page title for search |
| `seo_description` | str | Meta description |
| `source_video_url` | str | Original video link |

### Pricing Analyzer

**File:** `app/ai/pricing_analyzer.py`

#### `analyze_pricing(client, name, niche_tags, follower_count, pricing_tiers, content_types) → PricingAnalysis`
**File:** `app/ai/pricing_analyzer.py:39`

Analyzes competitor pricing and suggests KLIQ product tiers.

- Safety check: converts dollars to cents if model returns values < 100
- Fallback: Default Community ($9.99/mo) + Premium ($29.99/mo) if AI returns empty

**Output — `PricingAnalysis`:**
| Field | Type | Description |
|-------|------|-------------|
| `products` | list[SuggestedProduct] | Recommended products |
| `pricing_rationale` | str | Explanation of pricing strategy |

**`SuggestedProduct`:**
| Field | Type | Description |
|-------|------|-------------|
| `name` | str | Product name |
| `description` | str | Product description |
| `type` | str | "subscription" or "one_time" |
| `price_cents` | int | Price in cents |
| `currency` | str | Default: "USD" |
| `interval` | str? | "month", "year", or None |
| `features` | list[str] | Feature list |
| `recommended` | bool | Highlighted product |

### SEO Generator

**File:** `app/ai/seo_generator.py`

#### `generate_seo(client, name, store_name, tagline, specialties, niche_tags, location, content_titles) → GeneratedSEO`
**File:** `app/ai/seo_generator.py:32`

Generates SEO metadata for a KLIQ store.

- `seo_title` truncated to 60 chars
- `seo_description` truncated to 155 chars
- `seo_keywords` capped at 12
- `og_description` truncated to 200 chars
- Slug: sanitized to lowercase, hyphens only, max 50 chars

**Output — `GeneratedSEO`:**
| Field | Type | Description |
|-------|------|-------------|
| `seo_title` | str | Page title (max 60) |
| `seo_description` | str | Meta description (max 155) |
| `seo_keywords` | list[str] | Keywords (max 12) |
| `og_title` | str | Open Graph title |
| `og_description` | str | Open Graph description |
| `store_slug` | str | URL-safe slug (max 50) |

## Orchestration

The full AI pipeline is orchestrated by `generate_content_task` in `app/workers/ai_tasks.py`:

```
Bio → Blogs → Pricing → SEO → Colors
```

Each result is stored in the `generated_content` table with the appropriate `content_type` and JSON metadata in the `body` field.

## Configuration

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Claude API key |
