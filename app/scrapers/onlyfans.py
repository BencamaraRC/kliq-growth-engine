"""OnlyFans platform adapter.

Uses Playwright for browser-based scraping since OnlyFans has no public API.
Public profile pages (onlyfans.com/<username>) expose:
- Display name, bio, profile image, banner image
- Post count, media count, likes count
- Subscription pricing (free or paid tiers)
- Social links in bio

Note: Only scrapes publicly visible data from profile pages.
Does NOT require authentication — only reads public creator profiles.
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

OF_BASE = "https://onlyfans.com"

# Fitness/wellness search terms (used with third-party discovery, not OF search)
DEFAULT_DISCOVERY_QUERIES = [
    "fitness coach onlyfans",
    "personal trainer onlyfans",
    "yoga instructor onlyfans",
    "wellness coach onlyfans",
    "nutrition coach onlyfans",
]


class OnlyFansAdapter(PlatformAdapter):
    """OnlyFans platform adapter — Playwright-based public profile scraping."""

    @property
    def platform(self) -> Platform:
        return Platform.ONLYFANS

    async def discover_coaches(
        self,
        search_queries: list[str] | None = None,
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Discover fitness/wellness creators on OnlyFans.

        OnlyFans has no public search API. Discovery relies on:
        1. Third-party directories (fansmetrics, socialtracker, etc.)
        2. Cross-platform links (Instagram/TikTok bios linking to OF)
        3. Manual username lists

        For now, accepts a list of known usernames via search_queries.
        Each query is treated as a username to scrape.
        """
        queries = search_queries or []
        profiles = []

        for username in queries[:max_results]:
            username = username.strip().lstrip("@")
            if not username:
                continue
            try:
                profile = await self.scrape_profile(username)
                profiles.append(profile)
            except Exception as e:
                logger.warning(f"Failed to scrape OnlyFans profile @{username}: {e}")
                continue

        return profiles

    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape a public OnlyFans creator profile.

        Args:
            platform_id: OnlyFans username (without @).
        """
        url = f"{OF_BASE}/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 900},
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                # Wait for profile content to render
                await page.wait_for_timeout(3000)

                # Display name
                name = await _safe_text(
                    page,
                    ".g-user-name, .b-username__text, "
                    'h1[data-name], [class*="userName"]',
                )
                if not name:
                    name = platform_id

                # Bio / about text
                bio = await _safe_text(
                    page,
                    ".b-user-info__text, .b-tabs__nav + div p, "
                    '[class*="aboutText"], [class*="userBio"]',
                )

                # Profile image
                profile_img = await _safe_attr(
                    page,
                    ".g-avatar img, .b-profile__user img, "
                    'img[class*="avatar"], img[alt*="avatar"]',
                    "src",
                )

                # Banner / header image
                banner_img = await _safe_attr(
                    page,
                    '.b-profile__header img, [class*="headerImage"] img, '
                    '[class*="banner"] img, .b-profile-header-photo img',
                    "src",
                )
                # Fallback: try background-image on header div
                if not banner_img:
                    banner_img = await _extract_bg_image(
                        page,
                        '.b-profile__header, [class*="headerImage"], '
                        '[class*="banner"], .b-profile-header-photo',
                    )

                # Stats (posts, media, likes)
                stats = await _extract_stats(page)

                # Subscription price
                price_text = await _safe_text(
                    page,
                    ".b-offer-join__btn-text, [class*='subscribePrice'], "
                    "[class*='joinBtn'], .b-btn-subscribe",
                )

                # Extract email from bio
                email = None
                if bio:
                    email_match = re.search(
                        r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", bio
                    )
                    if email_match:
                        email = email_match.group()

                # Extract social links from bio
                social_links = await self.extract_social_links(bio or "")

                # Parse subscriber/follower counts from stats
                subscriber_count = stats.get("likes", 0)
                post_count = stats.get("posts", 0)
                media_count = stats.get("media", 0)

                return ScrapedProfile(
                    platform=Platform.ONLYFANS,
                    platform_id=platform_id,
                    name=name,
                    bio=bio or "",
                    profile_image_url=profile_img or "",
                    banner_image_url=banner_img or "",
                    email=email,
                    social_links=social_links,
                    subscriber_count=subscriber_count,
                    niche_tags=self._extract_niche_tags(f"{name} {bio}"),
                    raw_data={
                        "url": url,
                        "stats": stats,
                        "price_text": price_text,
                        "post_count": post_count,
                        "media_count": media_count,
                    },
                )

            finally:
                await browser.close()

    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape visible posts from a public OnlyFans profile.

        Only free/preview posts are accessible without a subscription.
        Most content is behind the paywall, so this returns limited results.
        """
        url = f"{OF_BASE}/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                # Scroll to load posts
                for _ in range(min(3, max_items // 5)):
                    await page.evaluate(
                        "window.scrollTo(0, document.body.scrollHeight)"
                    )
                    await page.wait_for_timeout(2000)

                # Extract visible post previews
                post_els = await page.query_selector_all(
                    ".b-post, [class*='postItem'], article"
                )
                content = []

                for post in post_els[:max_items]:
                    text = await _el_text(
                        post,
                        ".b-post__text, [class*='postText'], p",
                    )
                    likes = await _el_text(
                        post,
                        "[class*='likeCount'], .b-post__like-count",
                    )

                    # Check for media (images/videos)
                    media_el = await post.query_selector(
                        "img.b-post__image, video, [class*='postMedia'] img"
                    )
                    thumbnail = ""
                    if media_el:
                        thumbnail = (await media_el.get_attribute("src")) or ""

                    if text or thumbnail:
                        content.append(
                            ScrapedContent(
                                platform=Platform.ONLYFANS,
                                platform_id=platform_id,
                                content_type="post",
                                body=text or "",
                                url=url,
                                thumbnail_url=thumbnail,
                                engagement_count=_parse_number(likes),
                            )
                        )

                return content

            finally:
                await browser.close()

    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """Scrape subscription pricing from an OnlyFans profile.

        OnlyFans creators typically have:
        - Free subscription (with PPV content)
        - Monthly subscription ($X/month)
        - Bundle discounts (3/6/12 months)
        """
        url = f"{OF_BASE}/{platform_id}"

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                pricing = []

                # Main subscription price
                price_text = await _safe_text(
                    page,
                    ".b-offer-join__btn-text, [class*='subscribePrice'], "
                    ".b-btn-subscribe, [class*='joinBtn']",
                )

                price_info = _parse_of_price(price_text)

                if price_info["amount"] > 0:
                    pricing.append(
                        ScrapedPricing(
                            platform=Platform.ONLYFANS,
                            platform_id=platform_id,
                            tier_name="Monthly Subscription",
                            price_amount=price_info["amount"],
                            currency=price_info["currency"],
                            interval="month",
                        )
                    )
                elif "free" in (price_text or "").lower():
                    pricing.append(
                        ScrapedPricing(
                            platform=Platform.ONLYFANS,
                            platform_id=platform_id,
                            tier_name="Free Subscription",
                            price_amount=0,
                            currency="USD",
                            interval="month",
                        )
                    )

                # Bundle pricing (discount tiers)
                bundle_els = await page.query_selector_all(
                    ".b-offer-bundle, [class*='bundleItem'], "
                    "[class*='subscriptionBundle']"
                )
                for bundle in bundle_els:
                    duration = await _el_text(bundle, "[class*='duration'], .months")
                    bundle_price = await _el_text(
                        bundle, "[class*='price'], .amount"
                    )
                    discount = await _el_text(
                        bundle, "[class*='discount'], .save"
                    )

                    bp = _parse_of_price(bundle_price)
                    if bp["amount"] > 0:
                        months = _parse_number(duration) or 1
                        tier_name = f"{months} Month Bundle"
                        if discount:
                            tier_name += f" ({discount})"

                        pricing.append(
                            ScrapedPricing(
                                platform=Platform.ONLYFANS,
                                platform_id=platform_id,
                                tier_name=tier_name,
                                price_amount=bp["amount"],
                                currency=bp["currency"],
                                interval=f"{months}_months",
                                description=discount or "",
                            )
                        )

                return pricing

            finally:
                await browser.close()

    @staticmethod
    def _extract_niche_tags(text: str) -> list[str]:
        """Extract niche tags from bio text."""
        niche_keywords = {
            "fitness": ["fitness", "workout", "exercise", "training", "gym"],
            "yoga": ["yoga", "meditation", "mindfulness", "stretching"],
            "nutrition": ["nutrition", "diet", "meal prep", "macros", "recipes"],
            "strength": [
                "strength",
                "powerlifting",
                "weightlifting",
                "bodybuilding",
                "muscle",
            ],
            "cardio": ["cardio", "running", "hiit", "endurance"],
            "wellness": ["wellness", "health", "self-care", "holistic", "lifestyle"],
            "coaching": ["coaching", "coach", "personal trainer", "pt"],
            "dance": ["dance", "dancer", "choreography", "twerk"],
            "martial_arts": ["martial arts", "mma", "boxing", "kickboxing", "jiu jitsu"],
            "flexibility": ["flexibility", "contortion", "splits", "mobility"],
            "business": ["business coach", "entrepreneur", "startup", "business strategy", "consulting", "business mentor"],
            "marketing": ["marketing", "digital marketing", "social media marketing", "content creator", "branding", "sales funnel", "copywriting", "email marketing"],
            "money_online": ["make money online", "passive income", "affiliate marketing", "dropshipping", "ecommerce", "online business", "side hustle", "financial freedom"],
            "life_coaching": ["life coach", "life coaching", "mindset coach", "personal development", "personal growth", "motivational speaker", "manifestation", "accountability coach"],
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


async def _extract_bg_image(page, selector: str) -> str:
    """Extract background-image URL from an element's computed style."""
    try:
        result = await page.evaluate(
            """(selector) => {
                const el = document.querySelector(selector);
                if (!el) return '';
                const style = window.getComputedStyle(el);
                const bg = style.backgroundImage;
                const match = bg.match(/url\\(['"]?(.*?)['"]?\\)/);
                return match ? match[1] : '';
            }""",
            selector.split(",")[0].strip(),
        )
        return result or ""
    except Exception:
        return ""


async def _extract_stats(page) -> dict:
    """Extract profile stats (posts, media, likes) from the page."""
    stats = {"posts": 0, "media": 0, "likes": 0}
    try:
        stat_els = await page.query_selector_all(
            ".b-profile__sections__count, [class*='profileStat'], "
            ".b-tabs__nav__item"
        )
        for el in stat_els:
            text = (await el.inner_text()).strip().lower()
            number = _parse_number(text)
            if "post" in text:
                stats["posts"] = number
            elif "photo" in text or "video" in text or "media" in text:
                stats["media"] = number
            elif "like" in text:
                stats["likes"] = number
    except Exception:
        pass
    return stats


def _parse_number(text: str) -> int:
    """Parse a number from text like '12.5K' or '1,234'."""
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


def _parse_of_price(text: str) -> dict:
    """Parse OnlyFans pricing text like '$9.99/month' or 'FREE'."""
    if not text:
        return {"amount": 0, "currency": "USD"}

    if "free" in text.lower():
        return {"amount": 0, "currency": "USD"}

    currency_map = {"$": "USD", "\u00a3": "GBP", "\u20ac": "EUR"}
    currency = "USD"
    for symbol, code in currency_map.items():
        if symbol in text:
            currency = code
            break

    match = re.search(r"([\d,.]+)", text)
    amount = float(match.group(1).replace(",", "")) if match else 0

    return {"amount": amount, "currency": currency}
