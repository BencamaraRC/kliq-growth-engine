"""Stan.store platform adapter.

Stan.store is a creator commerce platform (competitor to KLIQ) used by
fitness coaches, business coaches, content creators, and life coaches to
sell digital products, courses, memberships, and coaching sessions.

Uses Playwright for scraping — no public API available.

Stan.store pages are structured as:
- Creator page: stan.store/<username> — profile, bio, product grid
- Products: digital downloads, courses, memberships, 1:1 coaching
- Pricing: displayed per-product on the creator page
"""

import logging
import re

from playwright.async_api import async_playwright

from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)

logger = logging.getLogger(__name__)

STAN_BASE = "https://stan.store"


class StanAdapter(PlatformAdapter):
    """Stan.store platform adapter — Playwright scraping."""

    @property
    def platform(self) -> Platform:
        return Platform.STAN

    async def discover_coaches(
        self,
        search_queries: list[str] | None = None,
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Discover coaches on Stan.store.

        Stan.store doesn't have a public search/discovery page, so we
        use Google site-search as the discovery mechanism.
        """
        queries = search_queries or [
            "fitness coach",
            "personal trainer",
            "business coach",
            "life coach",
            "marketing coach",
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
                    # Google site-search for Stan.store creators
                    search_url = (
                        f"https://www.google.com/search?q=site:stan.store+{query.replace(' ', '+')}"
                    )
                    await page.goto(search_url, wait_until="networkidle", timeout=30000)

                    # Extract Stan.store URLs from search results
                    links = await page.query_selector_all("a[href*='stan.store']")
                    for link in links:
                        href = await link.get_attribute("href") or ""
                        username = _extract_stan_username(href)
                        if not username or username in seen_ids:
                            continue
                        seen_ids.add(username)

                        profiles.append(
                            ScrapedProfile(
                                platform=Platform.STAN,
                                platform_id=username,
                                name=username,
                                raw_data={"source": "google_search", "query": query},
                            )
                        )

                        if len(profiles) >= max_results:
                            break

                except Exception as e:
                    logger.warning(f"Stan.store Google search failed for '{query}': {e}")
                finally:
                    await page.close()

            await browser.close()

        # Enrich top results with full profile data
        enriched = []
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            for profile in profiles[:max_results]:
                try:
                    full = await self._scrape_profile_with_browser(browser, profile.platform_id)
                    enriched.append(full)
                except Exception as e:
                    logger.warning(f"Failed to enrich Stan profile {profile.platform_id}: {e}")
                    enriched.append(profile)
            await browser.close()

        return enriched[:max_results]

    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape a Stan.store creator profile.

        Args:
            platform_id: Stan.store username (e.g., "fitcoachjane").
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                return await self._scrape_profile_with_browser(browser, platform_id)
            finally:
                await browser.close()

    async def _scrape_profile_with_browser(self, browser, platform_id: str) -> ScrapedProfile:
        """Scrape a Stan.store profile using an existing browser instance."""
        url = f"{STAN_BASE}/{platform_id}"
        page = await browser.new_page()

        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)

            # Creator name — usually in an h1 or prominent heading
            name = await _safe_text(page, "h1, [data-testid='creator-name']")

            # Bio / description
            bio = await _safe_text(
                page, "[data-testid='creator-bio'], .bio, .description, h1 + p, h1 + div p"
            )

            # Profile image
            profile_img = await _safe_attr(
                page,
                "img[alt*='profile'], img[alt*='avatar'], .profile-image img, header img",
                "src",
            )

            # Extract email from bio
            email = None
            full_text = f"{name} {bio}"
            email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", full_text)
            if email_match:
                email = email_match.group()

            # Extract social links from bio and page
            page_text = await page.inner_text("body")
            social_links = await self.extract_social_links(page_text or "")

            # Count products on the page
            product_els = await page.query_selector_all(
                "[data-testid='product-card'], .product-card, .product, a[href*='/p/']"
            )

            return ScrapedProfile(
                platform=Platform.STAN,
                platform_id=platform_id,
                name=name or platform_id,
                bio=bio or "",
                profile_image_url=profile_img or "",
                email=email,
                social_links=social_links,
                niche_tags=self._extract_niche_tags(full_text),
                raw_data={
                    "url": url,
                    "product_count": len(product_els),
                },
            )
        finally:
            await page.close()

    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape products/content from a Stan.store creator page.

        Stan.store products are the primary content — digital products,
        courses, memberships, and coaching sessions.
        """
        url = f"{STAN_BASE}/{platform_id}"
        content = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                # Extract product cards
                products = await page.query_selector_all(
                    "[data-testid='product-card'], .product-card, .product, a[href*='/p/']"
                )

                for product in products[:max_items]:
                    title = await _el_text(product, "h3, h4, .product-title, .title")
                    desc = await _el_text(product, "p, .product-description, .description")
                    img = await _el_attr(product, "img", "src")
                    href = await product.get_attribute("href") or ""

                    product_url = (
                        href if href.startswith("http") else f"{STAN_BASE}{href}" if href else url
                    )

                    if title:
                        content.append(
                            ScrapedContent(
                                platform=Platform.STAN,
                                platform_id=platform_id,
                                content_type="product",
                                title=title,
                                description=desc or "",
                                url=product_url,
                                thumbnail_url=img or "",
                            )
                        )

                return content

            finally:
                await browser.close()

    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """Scrape pricing from a Stan.store creator page.

        Stan.store displays prices per-product on the creator page.
        """
        url = f"{STAN_BASE}/{platform_id}"
        pricing = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)

                products = await page.query_selector_all(
                    "[data-testid='product-card'], .product-card, .product, a[href*='/p/']"
                )

                for product in products:
                    title = await _el_text(product, "h3, h4, .product-title, .title")
                    price_text = await _el_text(
                        product, ".price, [data-testid='price'], span:has-text('$')"
                    )

                    price_info = _parse_price(price_text)
                    if price_info.get("amount", 0) > 0:
                        pricing.append(
                            ScrapedPricing(
                                platform=Platform.STAN,
                                platform_id=platform_id,
                                tier_name=title or "Product",
                                price_amount=price_info["amount"],
                                currency=price_info.get("currency", "USD"),
                                interval=price_info.get("interval", "one_time"),
                            )
                        )

                return pricing

            finally:
                await browser.close()

    @staticmethod
    def _extract_niche_tags(text: str) -> list[str]:
        """Extract niche tags from text."""
        niche_keywords = {
            "fitness": ["fitness", "workout", "exercise", "training", "gym"],
            "yoga": ["yoga", "meditation", "mindfulness"],
            "nutrition": ["nutrition", "diet", "meal prep", "macros", "recipes"],
            "strength": ["strength", "powerlifting", "weightlifting", "bodybuilding"],
            "wellness": ["wellness", "health", "self-care", "holistic"],
            "coaching": ["coaching", "coach", "mentor"],
            "business": [
                "business coach",
                "entrepreneur",
                "startup",
                "business strategy",
                "consulting",
                "business mentor",
            ],
            "marketing": [
                "marketing",
                "digital marketing",
                "social media marketing",
                "content creator",
                "branding",
                "sales funnel",
                "copywriting",
                "email marketing",
            ],
            "money_online": [
                "make money online",
                "passive income",
                "affiliate marketing",
                "dropshipping",
                "ecommerce",
                "online business",
                "side hustle",
                "financial freedom",
            ],
            "life_coaching": [
                "life coach",
                "life coaching",
                "mindset coach",
                "personal development",
                "personal growth",
                "motivational speaker",
                "manifestation",
                "accountability coach",
            ],
        }
        text_lower = (text or "").lower()
        return [
            tag
            for tag, keywords in niche_keywords.items()
            if any(kw in text_lower for kw in keywords)
        ]


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


async def _el_attr(parent, selector: str, attr: str) -> str:
    """Safely extract an attribute from a child element."""
    try:
        el = await parent.query_selector(selector)
        if el:
            val = await el.get_attribute(attr)
            return val or ""
    except Exception:
        pass
    return ""


def _extract_stan_username(url: str) -> str | None:
    """Extract username from a Stan.store URL.

    Handles: stan.store/username, stan.store/username/p/product
    Excludes: stan.store/about, stan.store/pricing, etc.
    """
    if not url:
        return None
    match = re.search(r"stan\.store/([a-zA-Z0-9_-]+)", url)
    if not match:
        return None
    username = match.group(1).lower()
    # Filter out non-profile pages
    excluded = {"about", "pricing", "terms", "privacy", "login", "signup", "help", "blog", "p"}
    if username in excluded:
        return None
    return username


def _parse_price(text: str) -> dict:
    """Parse a price from text like '$29' or '$49.99/month'."""
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

    interval = "one_time"
    text_lower = text.lower()
    if "month" in text_lower or "/mo" in text_lower:
        interval = "month"
    elif "year" in text_lower or "/yr" in text_lower:
        interval = "year"

    return {"amount": amount, "currency": currency, "interval": interval}
