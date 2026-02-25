"""Generic website scraper (Phase 5 — stub).

Will use Playwright for JS-rendered pages + BeautifulSoup for static HTML.
Extracts blogs, images, brand colors, and structured data.
"""

from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)


class WebsiteAdapter(PlatformAdapter):
    @property
    def platform(self) -> Platform:
        return Platform.WEBSITE

    async def discover_coaches(self, search_queries, max_results=50):
        raise NotImplementedError("Website adapter not yet implemented (Phase 5)")

    async def scrape_profile(self, platform_id):
        raise NotImplementedError("Website adapter not yet implemented (Phase 5)")

    async def scrape_content(self, platform_id, max_items=20):
        raise NotImplementedError("Website adapter not yet implemented (Phase 5)")

    async def scrape_pricing(self, platform_id):
        raise NotImplementedError("Website adapter not yet implemented (Phase 5)")
