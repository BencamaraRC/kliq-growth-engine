"""Skool platform adapter.

Uses two scraping strategies:
1. Apify Skool scraper actor — for bulk discovery (reliable, fast)
2. Playwright fallback — for individual profile scraping when Apify is unavailable

Skool communities are structured as:
- Community page: name, description, member count, pricing
- Posts: community feed items (text + media)
- About: community description and rules
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

SKOOL_BASE = "https://www.skool.com"

# Fitness/wellness Skool search queries
DEFAULT_SKOOL_QUERIES = [
    "fitness coaching",
    "personal training",
    "yoga community",
    "wellness coaching",
    "nutrition coaching",
    "strength training",
    "online fitness",
]


class SkoolAdapter(PlatformAdapter):
    """Skool platform adapter — Apify + Playwright fallback."""

    def __init__(self, apify_token: str | None = None):
        self._apify_token = apify_token or settings.apify_api_token

    @property
    def platform(self) -> Platform:
        return Platform.SKOOL

    async def discover_coaches(
        self,
        search_queries: list[str] | None = None,
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Discover fitness communities on Skool.

        Strategy: Try Apify actor first, fall back to Playwright scraping.
        """
        queries = search_queries or DEFAULT_SKOOL_QUERIES

        if self._apify_token:
            try:
                return await self._discover_via_apify(queries, max_results)
            except Exception as e:
                logger.warning(f"Apify discovery failed, falling back to Playwright: {e}")

        return await self._discover_via_playwright(queries, max_results)

    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape a Skool community profile.

        Args:
            platform_id: Skool community slug (e.g., "fitness-coaching-hub").
        """
        url = f"{SKOOL_BASE}/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Extract community info
                name = await _safe_text(page, "h1")
                description = await _safe_text(page, '[data-testid="group-description"], .group-description, p.description')

                # Member count
                member_text = await _safe_text(page, '[data-testid="member-count"], .member-count')
                member_count = _parse_number(member_text)

                # Profile image
                profile_img = await _safe_attr(page, 'img[alt*="community"], img[alt*="group"], .group-avatar img', "src")

                # Extract email from description
                email = None
                if description:
                    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", description)
                    if email_match:
                        email = email_match.group()

                # Extract social links
                social_links = await self.extract_social_links(description or "")

                # Extract pricing from the page
                price_text = await _safe_text(page, '[data-testid="price"], .price, .pricing')
                pricing_info = _parse_price(price_text)

                return ScrapedProfile(
                    platform=Platform.SKOOL,
                    platform_id=platform_id,
                    name=name or platform_id,
                    bio=description or "",
                    profile_image_url=profile_img or "",
                    email=email,
                    social_links=social_links,
                    member_count=member_count,
                    niche_tags=self._extract_niche_tags(f"{name} {description}"),
                    raw_data={"url": url, "pricing": pricing_info},
                )

            finally:
                await browser.close()

    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape recent posts from a Skool community."""
        url = f"{SKOOL_BASE}/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Scroll to load more posts
                for _ in range(min(3, max_items // 10)):
                    await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    await page.wait_for_timeout(1500)

                # Extract posts
                posts = await page.query_selector_all('[data-testid="post"], .post-card, article')
                content = []

                for post in posts[:max_items]:
                    title = await _el_text(post, "h3, h2, .post-title")
                    body = await _el_text(post, "p, .post-body, .post-content")
                    likes = await _el_text(post, '[data-testid="like-count"], .like-count')

                    if title or body:
                        content.append(
                            ScrapedContent(
                                platform=Platform.SKOOL,
                                platform_id=platform_id,
                                content_type="post",
                                title=title or "",
                                body=body or "",
                                url=f"{url}",
                                engagement_count=_parse_number(likes),
                            )
                        )

                return content

            finally:
                await browser.close()

    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """Scrape pricing tiers from a Skool community.

        Skool communities typically have:
        - Free tier
        - Paid membership ($X/month)
        """
        url = f"{SKOOL_BASE}/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                pricing = []

                # Look for pricing elements
                price_elements = await page.query_selector_all(
                    '[data-testid="pricing-tier"], .pricing-card, .membership-tier'
                )

                if price_elements:
                    for el in price_elements:
                        name = await _el_text(el, "h3, h4, .tier-name")
                        price_text = await _el_text(el, ".price, .amount")
                        desc = await _el_text(el, "p, .description")

                        price_info = _parse_price(price_text)
                        if price_info.get("amount", 0) > 0:
                            pricing.append(
                                ScrapedPricing(
                                    platform=Platform.SKOOL,
                                    platform_id=platform_id,
                                    tier_name=name or "Membership",
                                    price_amount=price_info["amount"],
                                    currency=price_info.get("currency", "USD"),
                                    interval=price_info.get("interval", "month"),
                                    description=desc or "",
                                )
                            )
                else:
                    # Try to find a single price on the page
                    price_text = await _safe_text(page, '[data-testid="price"], .price')
                    price_info = _parse_price(price_text)
                    if price_info.get("amount", 0) > 0:
                        pricing.append(
                            ScrapedPricing(
                                platform=Platform.SKOOL,
                                platform_id=platform_id,
                                tier_name="Membership",
                                price_amount=price_info["amount"],
                                currency=price_info.get("currency", "USD"),
                                interval="month",
                            )
                        )

                return pricing

            finally:
                await browser.close()

    async def _discover_via_apify(
        self, queries: list[str], max_results: int
    ) -> list[ScrapedProfile]:
        """Discover communities using Apify Skool scraper actor."""
        profiles = []
        seen_ids = set()

        async with httpx.AsyncClient(timeout=60.0) as client:
            for query in queries:
                if len(profiles) >= max_results:
                    break

                # Run Apify actor
                response = await client.post(
                    "https://api.apify.com/v2/acts/apify~skool-scraper/runs",
                    headers={"Authorization": f"Bearer {self._apify_token}"},
                    json={
                        "searchQuery": query,
                        "maxResults": min(20, max_results - len(profiles)),
                    },
                )
                response.raise_for_status()
                run_data = response.json()
                run_id = run_data["data"]["id"]

                # Wait for results (poll)
                dataset_url = f"https://api.apify.com/v2/actor-runs/{run_id}/dataset/items"
                for _ in range(30):  # Max 5 min wait
                    import asyncio
                    await asyncio.sleep(10)

                    items_resp = await client.get(
                        dataset_url,
                        headers={"Authorization": f"Bearer {self._apify_token}"},
                    )
                    if items_resp.status_code == 200:
                        items = items_resp.json()
                        if items:
                            for item in items:
                                slug = item.get("slug", "")
                                if slug and slug not in seen_ids:
                                    seen_ids.add(slug)
                                    profiles.append(
                                        ScrapedProfile(
                                            platform=Platform.SKOOL,
                                            platform_id=slug,
                                            name=item.get("name", slug),
                                            bio=item.get("description", ""),
                                            profile_image_url=item.get("imageUrl", ""),
                                            member_count=item.get("memberCount", 0),
                                            niche_tags=self._extract_niche_tags(
                                                f"{item.get('name', '')} {item.get('description', '')}"
                                            ),
                                            raw_data=item,
                                        )
                                    )
                            break

        return profiles[:max_results]

    async def _discover_via_playwright(
        self, queries: list[str], max_results: int
    ) -> list[ScrapedProfile]:
        """Discover communities by searching Skool via Playwright."""
        profiles = []
        seen_ids = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            for query in queries:
                if len(profiles) >= max_results:
                    break

                page = await browser.new_page()
                try:
                    search_url = f"{SKOOL_BASE}/discovery?q={query.replace(' ', '+')}"
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)

                    # Extract community cards
                    cards = await page.query_selector_all(
                        '[data-testid="community-card"], .community-card, a[href*="/"]'
                    )

                    for card in cards:
                        href = await card.get_attribute("href")
                        if not href or not href.startswith("/"):
                            continue

                        slug = href.strip("/").split("/")[0]
                        if slug in seen_ids or not slug:
                            continue
                        seen_ids.add(slug)

                        name = await _el_text(card, "h3, h4, .name")
                        desc = await _el_text(card, "p, .description")
                        member_text = await _el_text(card, ".member-count, .members")

                        profiles.append(
                            ScrapedProfile(
                                platform=Platform.SKOOL,
                                platform_id=slug,
                                name=name or slug,
                                bio=desc or "",
                                member_count=_parse_number(member_text),
                                niche_tags=self._extract_niche_tags(f"{name} {desc}"),
                            )
                        )

                        if len(profiles) >= max_results:
                            break

                except Exception as e:
                    logger.warning(f"Skool search failed for '{query}': {e}")
                finally:
                    await page.close()

            await browser.close()

        return profiles[:max_results]

    @staticmethod
    def _extract_niche_tags(text: str) -> list[str]:
        """Extract fitness/wellness niche tags from text."""
        niche_keywords = {
            "fitness": ["fitness", "workout", "exercise", "training", "gym"],
            "yoga": ["yoga", "meditation", "mindfulness"],
            "nutrition": ["nutrition", "diet", "meal", "macros"],
            "strength": ["strength", "powerlifting", "weightlifting", "bodybuilding"],
            "wellness": ["wellness", "health", "self-care", "holistic"],
            "coaching": ["coaching", "coach", "mentor", "transformation"],
            "weight_loss": ["weight loss", "fat loss", "lean", "shred"],
        }
        text_lower = (text or "").lower()
        return [tag for tag, keywords in niche_keywords.items() if any(kw in text_lower for kw in keywords)]


# --- Playwright helpers ---


async def _safe_text(page, selector: str) -> str:
    """Safely extract text from a page element."""
    try:
        el = await page.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()
    except Exception:
        pass
    return ""


async def _safe_attr(page, selector: str, attr: str) -> str:
    """Safely extract an attribute from a page element."""
    try:
        el = await page.query_selector(selector)
        if el:
            val = await el.get_attribute(attr)
            return val or ""
    except Exception:
        pass
    return ""


async def _el_text(parent, selector: str) -> str:
    """Safely extract text from a child element."""
    try:
        el = await parent.query_selector(selector)
        if el:
            return (await el.inner_text()).strip()
    except Exception:
        pass
    return ""


def _parse_number(text: str) -> int:
    """Parse a number from text like '12.5K members' or '1,234'."""
    if not text:
        return 0
    text = text.strip().lower().replace(",", "")
    match = re.search(r"([\d.]+)\s*k", text)
    if match:
        return int(float(match.group(1)) * 1000)
    match = re.search(r"([\d.]+)\s*m", text)
    if match:
        return int(float(match.group(1)) * 1000000)
    match = re.search(r"(\d+)", text)
    if match:
        return int(match.group(1))
    return 0


def _parse_price(text: str) -> dict:
    """Parse a price from text like '$29/month' or '£49.99/year'."""
    if not text:
        return {"amount": 0}

    currency_map = {"$": "USD", "£": "GBP", "€": "EUR"}
    currency = "USD"
    for symbol, code in currency_map.items():
        if symbol in text:
            currency = code
            break

    match = re.search(r"([\d,.]+)", text)
    amount = float(match.group(1).replace(",", "")) if match else 0

    interval = "month"
    if "year" in text.lower() or "/yr" in text.lower():
        interval = "year"

    return {"amount": amount, "currency": currency, "interval": interval}
