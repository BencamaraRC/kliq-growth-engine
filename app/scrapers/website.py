"""Generic website scraper.

Uses Playwright for JS-rendered pages + BeautifulSoup for HTML parsing.
Extracts:
- Profile/about info (name, bio, image, contact)
- Blog posts (title, body, images)
- Brand colors from CSS and images
- Structured data (schema.org, Open Graph)

platform_id = the full URL of the website (e.g., "https://fitcoach.com")
"""

import logging
import re
from typing import Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)
from app.scrapers.color_extractor import extract_colors_from_url

logger = logging.getLogger(__name__)


class WebsiteAdapter(PlatformAdapter):
    """Generic website scraper using Playwright + BeautifulSoup."""

    @property
    def platform(self) -> Platform:
        return Platform.WEBSITE

    async def discover_coaches(
        self,
        search_queries: list[str] | None = None,
        max_results: int = 50,
    ) -> list[ScrapedProfile]:
        """Website adapter doesn't support discovery.

        Websites are discovered via cross-platform enrichment — when a
        YouTube channel or Skool community links to a personal website,
        the discovery orchestrator chains to this adapter.
        """
        logger.info("Website adapter doesn't support direct discovery — use cross-platform enrichment")
        return []

    async def scrape_profile(self, platform_id: str) -> ScrapedProfile:
        """Scrape profile info from a website.

        Args:
            platform_id: Full website URL (e.g., "https://fitcoach.com").
        """
        url = _normalize_url(platform_id)

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            try:
                await page.goto(url, wait_until="networkidle", timeout=30000)
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")

                # Extract name from various sources
                name = (
                    _og_content(soup, "og:site_name")
                    or _og_content(soup, "og:title")
                    or _meta_content(soup, "author")
                    or _tag_text(soup, "h1")
                    or urlparse(url).netloc
                )

                # Extract bio/description
                bio = (
                    _og_content(soup, "og:description")
                    or _meta_content(soup, "description")
                    or ""
                )

                # Try to find an about page for a richer bio
                about_bio = await self._scrape_about_page(browser, url, soup)
                if about_bio and len(about_bio) > len(bio):
                    bio = about_bio

                # Extract profile image
                profile_image = (
                    _og_content(soup, "og:image")
                    or _find_logo(soup, url)
                    or ""
                )

                # Extract email
                email = _extract_email(soup.get_text())

                # Extract social links
                social_links = _extract_social_links_from_soup(soup)

                # Extract brand colors from CSS
                brand_colors = await self._extract_brand_colors(page, profile_image)

                return ScrapedProfile(
                    platform=Platform.WEBSITE,
                    platform_id=platform_id,
                    name=name,
                    bio=bio,
                    profile_image_url=profile_image,
                    email=email,
                    website_url=url,
                    social_links=social_links,
                    brand_colors=brand_colors,
                    niche_tags=self._extract_niche_tags(f"{name} {bio}"),
                )

            finally:
                await browser.close()

    async def scrape_content(
        self,
        platform_id: str,
        max_items: int = 20,
    ) -> list[ScrapedContent]:
        """Scrape blog posts from a website."""
        url = _normalize_url(platform_id)
        content = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                # Find blog page
                blog_url = await self._find_blog_url(browser, url)
                if not blog_url:
                    logger.info(f"No blog page found on {url}")
                    await browser.close()
                    return []

                page = await browser.new_page()
                await page.goto(blog_url, wait_until="networkidle", timeout=30000)
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")

                # Find blog post links
                post_links = _find_blog_post_links(soup, url)

                for post_url in post_links[:max_items]:
                    try:
                        post = await self._scrape_single_post(browser, post_url)
                        if post:
                            content.append(post)
                    except Exception as e:
                        logger.debug(f"Failed to scrape post {post_url}: {e}")

                await page.close()

            finally:
                await browser.close()

        return content

    async def scrape_pricing(self, platform_id: str) -> list[ScrapedPricing]:
        """Scrape pricing from a website's pricing page."""
        url = _normalize_url(platform_id)
        pricing = []

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)

            try:
                pricing_url = await self._find_pricing_url(browser, url)
                if not pricing_url:
                    await browser.close()
                    return []

                page = await browser.new_page()
                await page.goto(pricing_url, wait_until="networkidle", timeout=30000)
                html = await page.content()
                soup = BeautifulSoup(html, "lxml")

                # Look for pricing cards/tables
                price_containers = soup.find_all(
                    class_=re.compile(r"pric|tier|plan|package", re.I)
                )

                for container in price_containers:
                    name = _tag_text(container, "h3") or _tag_text(container, "h2") or "Plan"
                    price_text = container.get_text()
                    price_match = re.search(r"[\$£€]([\d,.]+)", price_text)

                    if price_match:
                        amount = float(price_match.group(1).replace(",", ""))
                        currency = "USD"
                        if "£" in price_text:
                            currency = "GBP"
                        elif "€" in price_text:
                            currency = "EUR"

                        interval = "month"
                        if "year" in price_text.lower() or "annual" in price_text.lower():
                            interval = "year"

                        # Extract benefits
                        benefits = [li.get_text(strip=True) for li in container.find_all("li")]

                        pricing.append(
                            ScrapedPricing(
                                platform=Platform.WEBSITE,
                                platform_id=platform_id,
                                tier_name=name,
                                price_amount=amount,
                                currency=currency,
                                interval=interval,
                                benefits=benefits[:10],
                            )
                        )

                await page.close()

            finally:
                await browser.close()

        return pricing

    async def _scrape_about_page(self, browser, base_url: str, home_soup: BeautifulSoup) -> str:
        """Try to find and scrape an About page for a richer bio."""
        about_link = None
        for a in home_soup.find_all("a", href=True):
            href = a["href"].lower()
            text = a.get_text().lower()
            if "about" in href or "about" in text:
                about_link = urljoin(base_url, a["href"])
                break

        if not about_link:
            return ""

        try:
            page = await browser.new_page()
            await page.goto(about_link, wait_until="networkidle", timeout=20000)
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")
            await page.close()

            # Get the main content
            main = soup.find("main") or soup.find("article") or soup.find(class_=re.compile(r"content|about", re.I))
            if main:
                return main.get_text(separator=" ", strip=True)[:2000]
            return ""

        except Exception:
            return ""

    async def _find_blog_url(self, browser, base_url: str) -> str | None:
        """Find the blog page URL on a website."""
        page = await browser.new_page()
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=20000)
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                text = a.get_text().lower()
                if any(kw in href or kw in text for kw in ["blog", "articles", "posts", "news"]):
                    return urljoin(base_url, a["href"])

            # Try common blog paths
            for path in ["/blog", "/articles", "/posts", "/news"]:
                test_url = urljoin(base_url, path)
                resp = await page.goto(test_url, timeout=10000)
                if resp and resp.status == 200:
                    return test_url

        except Exception:
            pass
        finally:
            await page.close()

        return None

    async def _find_pricing_url(self, browser, base_url: str) -> str | None:
        """Find the pricing page URL on a website."""
        page = await browser.new_page()
        try:
            await page.goto(base_url, wait_until="networkidle", timeout=20000)
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            for a in soup.find_all("a", href=True):
                href = a["href"].lower()
                text = a.get_text().lower()
                if any(kw in href or kw in text for kw in ["pricing", "plans", "packages", "membership"]):
                    return urljoin(base_url, a["href"])

        except Exception:
            pass
        finally:
            await page.close()

        return None

    async def _scrape_single_post(self, browser, post_url: str) -> ScrapedContent | None:
        """Scrape a single blog post."""
        page = await browser.new_page()
        try:
            await page.goto(post_url, wait_until="networkidle", timeout=20000)
            html = await page.content()
            soup = BeautifulSoup(html, "lxml")

            title = (
                _og_content(soup, "og:title")
                or _tag_text(soup, "h1")
                or ""
            )

            # Find main content area
            article = soup.find("article") or soup.find("main") or soup.find(class_=re.compile(r"post|article|content|entry", re.I))
            body = article.get_text(separator=" ", strip=True)[:5000] if article else ""

            if not title and not body:
                return None

            thumbnail = _og_content(soup, "og:image") or ""

            # Extract published date
            date = _og_content(soup, "article:published_time") or ""
            if not date:
                time_el = soup.find("time")
                if time_el:
                    date = time_el.get("datetime", time_el.get_text(strip=True))

            description = _og_content(soup, "og:description") or _meta_content(soup, "description") or ""

            return ScrapedContent(
                platform=Platform.WEBSITE,
                platform_id=post_url,
                content_type="blog",
                title=title,
                description=description,
                body=body,
                url=post_url,
                thumbnail_url=thumbnail,
                published_at=date or None,
            )

        except Exception as e:
            logger.debug(f"Failed to scrape {post_url}: {e}")
            return None
        finally:
            await page.close()

    async def _extract_brand_colors(self, page, image_url: str) -> list[str]:
        """Extract brand colors from CSS variables and/or profile image."""
        colors = []

        # Try CSS custom properties
        try:
            css_colors = await page.evaluate("""() => {
                const style = getComputedStyle(document.documentElement);
                const vars = ['--primary', '--primary-color', '--brand', '--brand-color',
                              '--accent', '--accent-color', '--main-color', '--theme-color'];
                const found = [];
                for (const v of vars) {
                    const val = style.getPropertyValue(v).trim();
                    if (val && val.startsWith('#')) found.push(val);
                }
                return found;
            }""")
            colors.extend(css_colors)
        except Exception:
            pass

        # Fall back to image extraction
        if not colors and image_url:
            from app.scrapers.color_extractor import extract_colors_from_url as ecfu
            brand = await ecfu(image_url)
            if brand:
                colors = brand.palette

        return colors[:6]

    @staticmethod
    def _extract_niche_tags(text: str) -> list[str]:
        niche_keywords = {
            "fitness": ["fitness", "workout", "exercise", "training", "gym"],
            "yoga": ["yoga", "meditation", "mindfulness"],
            "nutrition": ["nutrition", "diet", "meal", "macros"],
            "strength": ["strength", "powerlifting", "weightlifting"],
            "wellness": ["wellness", "health", "self-care", "holistic"],
            "coaching": ["coaching", "coach", "mentor"],
        }
        text_lower = (text or "").lower()
        return [tag for tag, keywords in niche_keywords.items() if any(kw in text_lower for kw in keywords)]


# --- Utility helpers ---


def _normalize_url(url: str) -> str:
    """Ensure URL has a scheme."""
    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"
    return url


def _og_content(soup: BeautifulSoup, prop: str) -> str:
    """Get Open Graph meta content."""
    tag = soup.find("meta", property=prop) or soup.find("meta", attrs={"name": prop})
    return tag["content"].strip() if tag and tag.get("content") else ""


def _meta_content(soup: BeautifulSoup, name: str) -> str:
    """Get meta tag content by name."""
    tag = soup.find("meta", attrs={"name": name})
    return tag["content"].strip() if tag and tag.get("content") else ""


def _tag_text(soup_or_el, tag: str) -> str:
    """Get text content of the first matching tag."""
    el = soup_or_el.find(tag)
    return el.get_text(strip=True) if el else ""


def _extract_email(text: str) -> str | None:
    """Extract first email address from text."""
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
    return match.group() if match else None


def _extract_social_links_from_soup(soup: BeautifulSoup) -> dict:
    """Extract social media links from page HTML."""
    links = {}
    patterns = {
        "instagram": r"instagram\.com/([a-zA-Z0-9_.]+)",
        "tiktok": r"tiktok\.com/@([a-zA-Z0-9_.]+)",
        "youtube": r"youtube\.com/(?:@|channel/|c/)([a-zA-Z0-9_-]+)",
        "twitter": r"(?:twitter|x)\.com/([a-zA-Z0-9_]+)",
        "facebook": r"facebook\.com/([a-zA-Z0-9.]+)",
        "linkedin": r"linkedin\.com/in/([a-zA-Z0-9_-]+)",
        "skool": r"skool\.com/([a-zA-Z0-9_-]+)",
        "patreon": r"patreon\.com/([a-zA-Z0-9_-]+)",
    }

    for a in soup.find_all("a", href=True):
        href = a["href"]
        for platform_name, pattern in patterns.items():
            if platform_name not in links:
                match = re.search(pattern, href, re.I)
                if match:
                    links[platform_name] = match.group(0)

    return links


def _find_blog_post_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Find blog post URLs from a blog listing page."""
    post_links = []
    seen = set()

    # Look for article links
    for article in soup.find_all(["article", "div"], class_=re.compile(r"post|article|entry|blog", re.I)):
        a = article.find("a", href=True)
        if a:
            url = urljoin(base_url, a["href"])
            if url not in seen:
                seen.add(url)
                post_links.append(url)

    # If no articles found, look for links in a main/content area
    if not post_links:
        main = soup.find("main") or soup.find(class_=re.compile(r"blog|posts|content", re.I))
        if main:
            for a in main.find_all("a", href=True):
                url = urljoin(base_url, a["href"])
                # Filter out navigation/footer links
                if url not in seen and urlparse(url).netloc == urlparse(base_url).netloc:
                    path = urlparse(url).path
                    if len(path) > 5 and path.count("/") >= 2:
                        seen.add(url)
                        post_links.append(url)

    return post_links
