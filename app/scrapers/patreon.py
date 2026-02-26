"""Patreon platform adapter.

Uses the Patreon API v2 for:
- Creator profile data (name, bio, image, social links)
- Tier/pricing information (public tiers with benefits)
- Public posts (text content for blog conversion)

Discovery is limited — Patreon has no search API, so we rely on:
1. Cross-platform enrichment (YouTube bio links to Patreon)
2. Google search for "site:patreon.com fitness coach" via Playwright
"""

import logging
import re
from typing import Optional

import httpx
from playwright.async_api import async_playwright

from app.config import settings
from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)

logger = logging.getLogger(__name__)

PATREON_API_BASE = "https://www.patreon.com/api"


class PatreonAdapter(PlatformAdapter):
    """Patreon platform adapter using API v2 + web scraping fallback."""

    def __init__(self, access_token: str | None = None):
        self._token = access_token
        # Patreon public API endpoints don't always require auth

    @property
    def platform(self) -> Platform:
        return Platform.PATREON

    async def discover_coaches(
        self,
        search_queries: list[str] | None = None,
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Discover fitness creators on Patreon.

        Patreon has no public search API, so we scrape the discovery page
        or use Google site search.
        """
        queries = search_queries or [
            "fitness coach",
            "personal trainer",
            "yoga instructor",
            "wellness",
        ]

        profiles = []
        seen_ids = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for query in queries:
                if len(profiles) >= max_results:
                    break

                page = await browser.new_page()
                try:
                    # Use Patreon's search/discovery
                    url = f"https://www.patreon.com/search?q={query.replace(' ', '%20')}"
                    await page.goto(url, wait_until="networkidle", timeout=30000)

                    # Extract creator cards
                    cards = await page.query_selector_all(
                        '[data-tag="creator-card"], a[href*="/c/"], a[href*="patreon.com/"][data-tag]'
                    )

                    for card in cards:
                        href = await card.get_attribute("href") or ""
                        # Extract creator slug
                        slug = _extract_patreon_slug(href)
                        if not slug or slug in seen_ids:
                            continue
                        seen_ids.add(slug)

                        name = await _el_text(card, "h3, h2, .creator-name, [data-tag='creator-name']")
                        desc = await _el_text(card, "p, .creator-description")
                        img = await _el_attr(card, "img", "src")

                        profiles.append(
                            ScrapedProfile(
                                platform=Platform.PATREON,
                                platform_id=slug,
                                name=name or slug,
                                bio=desc or "",
                                profile_image_url=img or "",
                                niche_tags=self._extract_niche_tags(f"{name} {desc}"),
                            )
                        )

                        if len(profiles) >= max_results:
                            break

                except Exception as e:
                    logger.warning(f"Patreon search failed for '{query}': {e}")
                finally:
                    await page.close()

            await browser.close()

        return profiles[:max_results]

    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape a Patreon creator's profile.

        Uses the public API endpoint where possible, falls back to Playwright.
        """
        # Try public API first (no auth needed for public data)
        try:
            return await self._scrape_profile_api(platform_id)
        except Exception as e:
            logger.info(f"API scrape failed for {platform_id}, falling back to Playwright: {e}")

        return await self._scrape_profile_playwright(platform_id)

    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape public posts from a Patreon creator."""
        url = f"https://www.patreon.com/{platform_id}/posts"
        content = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Scroll for more content
                for _ in range(min(3, max_items // 10)):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                posts = await page.query_selector_all(
                    '[data-tag="post-card"], article, .post-card'
                )

                for post in posts[:max_items]:
                    title = await _el_text(post, "h2, h3, [data-tag='post-title']")
                    body = await _el_text(post, "[data-tag='post-content'], .post-content, p")
                    date = await _el_text(post, "time, [data-tag='post-date']")
                    likes = await _el_text(post, "[data-tag='like-count'], .like-count")
                    img = await _el_attr(post, "img", "src")

                    if title or body:
                        content.append(
                            ScrapedContent(
                                platform=Platform.PATREON,
                                platform_id=platform_id,
                                content_type="post",
                                title=title or "",
                                body=body or "",
                                url=f"https://www.patreon.com/{platform_id}/posts",
                                thumbnail_url=img or "",
                                published_at=date or None,
                                engagement_count=_parse_number(likes),
                            )
                        )

            except Exception as e:
                logger.warning(f"Content scraping failed for {platform_id}: {e}")
            finally:
                await browser.close()

        return content

    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """Scrape membership tiers from a Patreon creator."""
        url = f"https://www.patreon.com/{platform_id}"
        pricing = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                tiers = await page.query_selector_all(
                    '[data-tag="reward-tier"], .reward-tier, [data-tag="tier-card"]'
                )

                for tier in tiers:
                    name = await _el_text(tier, "h3, h2, [data-tag='tier-name']")
                    price_text = await _el_text(tier, "[data-tag='tier-price'], .tier-price, .amount")
                    desc = await _el_text(tier, "p, [data-tag='tier-description']")

                    # Parse benefits
                    benefit_els = await tier.query_selector_all("li, [data-tag='benefit']")
                    benefits = []
                    for b in benefit_els:
                        text = await _el_text_direct(b)
                        if text:
                            benefits.append(text)

                    price = _parse_patreon_price(price_text)
                    if price > 0:
                        pricing.append(
                            ScrapedPricing(
                                platform=Platform.PATREON,
                                platform_id=platform_id,
                                tier_name=name or "Membership",
                                price_amount=price,
                                currency="USD",
                                interval="month",
                                description=desc or "",
                                benefits=benefits,
                            )
                        )

            except Exception as e:
                logger.warning(f"Pricing scraping failed for {platform_id}: {e}")
            finally:
                await browser.close()

        return pricing

    async def _scrape_profile_api(self, platform_id: str) -> ScrapedProfile:
        """Attempt to get profile via Patreon's public-facing API."""
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Public campaign endpoint (no auth needed for some data)
            resp = await client.get(
                f"https://www.patreon.com/api/campaigns?filter[creator_vanity]={platform_id}"
                "&fields[campaign]=creation_name,summary,image_small_url,patron_count"
                "&fields[user]=full_name,about,image_url,social_connections"
            )
            resp.raise_for_status()
            data = resp.json()

            campaigns = data.get("data", [])
            if not campaigns:
                raise ValueError(f"No campaign found for {platform_id}")

            campaign = campaigns[0]
            attrs = campaign.get("attributes", {})

            return ScrapedProfile(
                platform=Platform.PATREON,
                platform_id=platform_id,
                name=attrs.get("creation_name", platform_id),
                bio=attrs.get("summary", ""),
                profile_image_url=attrs.get("image_small_url", ""),
                member_count=attrs.get("patron_count", 0),
                niche_tags=self._extract_niche_tags(
                    f"{attrs.get('creation_name', '')} {attrs.get('summary', '')}"
                ),
                raw_data=campaign,
            )

    async def _scrape_profile_playwright(self, platform_id: str) -> ScrapedProfile:
        """Fallback profile scraping via Playwright."""
        url = f"https://www.patreon.com/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                name = await _safe_text(page, "h1, [data-tag='creator-name']")
                bio = await _safe_text(page, "[data-tag='creator-about'], .about-section, .summary")
                img = await _safe_attr(page, "img[alt*='profile'], img[alt*='creator'], .avatar img", "src")
                patron_text = await _safe_text(page, "[data-tag='patron-count'], .patron-count")

                email = None
                if bio:
                    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", bio)
                    if email_match:
                        email = email_match.group()

                social_links = await self.extract_social_links(bio or "")

                return ScrapedProfile(
                    platform=Platform.PATREON,
                    platform_id=platform_id,
                    name=name or platform_id,
                    bio=bio or "",
                    profile_image_url=img or "",
                    email=email,
                    social_links=social_links,
                    member_count=_parse_number(patron_text),
                    niche_tags=self._extract_niche_tags(f"{name} {bio}"),
                )

            finally:
                await browser.close()

    @staticmethod
    def _extract_niche_tags(text: str) -> list[str]:
        """Extract fitness/wellness niche tags."""
        niche_keywords = {
            "fitness": ["fitness", "workout", "exercise", "training"],
            "yoga": ["yoga", "meditation", "mindfulness"],
            "nutrition": ["nutrition", "diet", "meal prep", "macros"],
            "strength": ["strength", "powerlifting", "weightlifting"],
            "wellness": ["wellness", "health", "self-care"],
            "coaching": ["coaching", "coach", "mentor"],
        }
        text_lower = (text or "").lower()
        return [tag for tag, keywords in niche_keywords.items() if any(kw in text_lower for kw in keywords)]


# --- Helpers ---


def _extract_patreon_slug(url: str) -> str | None:
    """Extract creator slug from a Patreon URL."""
    if not url:
        return None
    # Handle: /c/creatorname, /creatorname, patreon.com/creatorname
    match = re.search(r"patreon\.com/(?:c/)?([a-zA-Z0-9_-]+)", url)
    if match:
        slug = match.group(1)
        if slug not in ("posts", "about", "membership", "search", "login", "signup"):
            return slug
    # Handle relative paths
    match = re.search(r"^/(?:c/)?([a-zA-Z0-9_-]+)", url)
    if match:
        slug = match.group(1)
        if slug not in ("posts", "about", "membership", "search", "login", "signup"):
            return slug
    return None


async def _safe_text(page, selector: str) -> str:
    try:
        el = await page.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()
    except Exception:
        pass
    return ""


async def _safe_attr(page, selector: str, attr: str) -> str:
    try:
        el = await page.query_selector(selector)
        if el:
            return (await el.get_attribute(attr)) or ""
    except Exception:
        pass
    return ""


async def _el_text(parent, selector: str) -> str:
    try:
        el = await parent.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()
    except Exception:
        pass
    return ""


async def _el_text_direct(el) -> str:
    try:
        return (await el.inner_text()).strip()
    except Exception:
        return ""


async def _el_attr(parent, selector: str, attr: str) -> str:
    try:
        el = await parent.query_selector(selector)
        if el:
            return (await el.get_attribute(attr)) or ""
    except Exception:
        pass
    return ""


def _parse_number(text: str) -> int:
    if not text:
        return 0
    text = text.strip().lower().replace(",", "")
    match = re.search(r"([\d.]+)\s*k", text)
    if match:
        return int(float(match.group(1)) * 1000)
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else 0


def _parse_patreon_price(text: str) -> float:
    """Parse price from Patreon tier text like '$5 per month'."""
    if not text:
        return 0.0
    match = re.search(r"[\$£€]([\d,.]+)", text)
    return float(match.group(1).replace(",", "")) if match else 0.0
