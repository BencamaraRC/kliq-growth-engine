# KLIQ Growth Engine — Marketing Brief

## What is KLIQ?

KLIQ is a white-label platform that gives fitness and wellness coaches their own branded mobile app and webstore. Coaches get: a customisable app (iOS + Android), a webstore, subscription billing via Stripe, community features, content library, live streaming, and a coach admin dashboard.

**The problem:** 91% of coaches who sign up churn within 90 days. 98.5% generate zero revenue. Most coaches never get past setup.

**The Growth Engine solves this** by flipping the onboarding model: instead of asking coaches to build their store from scratch, we build it *for* them using AI — then invite them to claim it.

---

## How the Machine Works

### Step 1: Discover coaches (automated, daily)

We scan competitor platforms to find coaches who are already selling digital products, courses, or memberships elsewhere. The system searches for:

- Fitness coaches, personal trainers, yoga instructors
- Wellness coaches, nutrition coaches, health coaches
- Strength coaches, pilates instructors, CrossFit coaches
- Life coaches, business coaches, marketing coaches

**Platforms we scrape:**

| Platform | What we find | How |
|----------|-------------|-----|
| **YouTube** | Coaches with channels, subscribers, video content | YouTube Data API — channel search + video metadata + full transcripts |
| **Stan.store** | Coaches selling digital products (direct competitor) | Google site-search + page scraping |
| **Skool** | Coaches running paid communities | Apify scraper + community search |
| **Websites** | Additional data from coach's own site | Playwright browser automation |

We discover ~50 new coaches per day across platforms.

### Step 2: Scrape everything about them

For each coach we collect:

**Profile data:**
- Name, email, bio, profile photo, banner image
- Follower/subscriber count
- Website URL, all social links (Instagram, TikTok, Twitter, Facebook, LinkedIn)
- Niche tags (fitness, yoga, nutrition, strength, wellness, etc.)
- Brand colours (extracted from their profile image and CSS)
- Location (when available)

**Content data:**
- Up to 20 recent YouTube videos with full transcripts (free via transcript API)
- View counts, engagement (likes + comments), tags, publish dates
- Stan.store product listings (title, description, price, thumbnail)
- Skool community posts and member counts
- Website blog posts and about page content

**Pricing data:**
- Every pricing tier they offer (name, price, currency, interval)
- Benefits/features per tier
- Member counts for community products

### Step 3: AI builds their KLIQ store

Using Claude (Anthropic's AI), we generate a complete, branded store for each coach:

1. **Bio & copy** — tagline, short bio, full about page, specialties, coaching style description
2. **Blog posts** — up to 5 blog articles converted from their best-performing YouTube videos (by view count), with full HTML formatting
3. **Products & pricing** — AI analyses their competitor pricing and suggests KLIQ products (subscriptions, one-time purchases) with competitive pricing
4. **SEO metadata** — title, description, keywords, Open Graph tags, URL slug
5. **Brand theme** — 30+ colour fields applied across the entire app (buttons, backgrounds, navigation, overlays) based on their existing brand palette

The store is a real, fully functional KLIQ application — identical to what a paying coach gets.

### Step 4: Email outreach (automated, 7-step sequence)

| Step | Email | When | Goal |
|------|-------|------|------|
| 1 | "Your KLIQ store is ready!" | Immediately | Show them their pre-built store |
| 2 | "Your store is waiting for you" | Day 3 | First reminder if unclaimed |
| 3 | "Last chance to claim {store}" | Day 7 | Urgency/final reminder |
| 4 | "Welcome to KLIQ!" | On claim | Confirmation + next steps |
| 5 | "Review your store content" | Day +1 after claim | Get them to check AI content |
| 6 | "Start earning with Stripe" | Day +3 after claim | Connect payments |
| 7 | "Share with your first client" | Day +7 after claim | Drive first revenue |

Emails are personalised with: coach's name, store name, source platform, brand colour, store preview link, and a unique claim URL.

Steps 5-7 are skipped automatically if the coach has already completed that action.

### Step 5: Coach claims their store

When a coach clicks their claim link, they:
1. Set a password (30 seconds)
2. Get redirected to a welcome page showing their store
3. Review AI-generated content (can edit later in their dashboard)
4. Connect Stripe to start accepting payments
5. Share their store URL with clients

The store goes live immediately on claim. They get a branded URL: `{their-name}.joinkliq.io`

---

## Who We Target

### Ideal coach profile
- Already selling digital products, courses, or coaching online
- Has an audience (YouTube subscribers, Skool members, social following)
- Currently using a competitor platform (Stan.store, Skool, Patreon, Kajabi)
- Fitness, wellness, nutrition, yoga, strength, or lifestyle niche
- Has discoverable email (in bio, website, or about page)

### Ranking logic
Coaches are prioritised by:
1. Has a discoverable email address (required for outreach)
2. Total follower count across all platforms (bigger audience = higher value)

### Deduplication
We avoid contacting the same person twice using:
- Email matching
- Website URL matching
- Fuzzy name matching (85% similarity threshold)

---

## Competitor Landscape

These are the platforms our target coaches currently use — and where we find them:

| Platform | What they offer | How coaches use it | Our angle |
|----------|----------------|-------------------|-----------|
| **Stan.store** | Link-in-bio commerce, digital products, courses, memberships | Sell ebooks, coaching calls, courses via a simple storefront | KLIQ offers a full branded app + webstore vs a simple link page |
| **Skool** | Community + courses | Run paid community groups with course content | KLIQ includes community features plus a full app, content library, live streaming |
| **Patreon** | Membership subscriptions | Monthly subscription tiers for exclusive content | KLIQ offers white-label branding vs Patreon's marketplace |
| **Kajabi** | Online courses + website builder | Build course websites and sales funnels | KLIQ adds a native mobile app on top of web |
| **Teachable/Thinkific** | Course platforms | Host and sell online courses | KLIQ bundles courses with community, live sessions, and an app |

### Key differentiator
None of these competitors give coaches a branded native mobile app. KLIQ does — iOS and Android, with their name, logo, and colours.

---

## What Data We Have for Each Coach

By the time a store is built, we have a rich profile:

**Contact & identity:** Name, email, profile photo, banner image, website, all social links

**Audience metrics:** YouTube subscribers, Skool members, total follower count, video view counts, engagement rates

**Content library:** Up to 20 video transcripts, blog posts, product descriptions, community posts

**Pricing intelligence:** Every pricing tier on their competitor platform — price, currency, interval, features, member count

**Brand assets:** Primary/secondary/accent colours, profile image, banner image

**Niche classification:** Tagged with specific niches (fitness, yoga, nutrition, strength, wellness, pilates, crossfit, etc.)

**Platform footprint:** Which platforms they're active on, cross-platform social links

---

## Current Pipeline Status

| Metric | Value |
|--------|-------|
| Prospects discovered | 69 (from initial test runs) |
| Platforms active | YouTube, Stan.store, Skool |
| Daily discovery capacity | ~50 coaches/day |
| AI store generation | ~5 minutes per coach |
| Email sequence | 7 steps, fully automated |
| Outreach frequency | Every 30 minutes |
| Discovery frequency | Daily at 6 AM UTC |

---

## System URLs

| Service | URL |
|---------|-----|
| API | https://kliq-growth-api-512447837673.europe-west1.run.app |
| Dashboard | https://kliq-growth-dashboard-512447837673.europe-west1.run.app |
| Store preview | `https://kliq-growth-api-.../preview/{prospect_id}` |
| Claim flow | `https://kliq-growth-api-.../claim?token={token}` |
| Outreach sender | growth@joinkliq.io (via Brevo) |

---

## What We Need From Marketing

1. **Outreach copy refinement** — the 7 email templates can be customised. Current subjects and body copy are functional but could be stronger.

2. **Search query expansion** — we can add any search terms to find coaches in new niches or geographies.

3. **Landing page / claim flow optimisation** — the claim experience (password set → welcome → review → Stripe) could benefit from conversion optimisation.

4. **Targeting strategy** — which coach segments should we prioritise? High-follower YouTube creators? Small-but-engaged Skool community leaders? Stan.store power users?

5. **Competitor positioning** — how do we frame the "we already built your store" pitch against each competitor platform?

6. **Scale planning** — at 50 coaches/day discovery, we'll have ~1,500/month in the pipeline. What's the right outreach volume and cadence?
