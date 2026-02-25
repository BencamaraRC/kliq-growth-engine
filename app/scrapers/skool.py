"""Skool platform adapter (Phase 5 — stub).

Will use Apify pre-built Skool scraper + Playwright fallback.
"""

from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)


class SkoolAdapter(PlatformAdapter):
    @property
    def platform(self) -> Platform:
        return Platform.SKOOL

    async def discover_coaches(self, search_queries, max_results=50):
        raise NotImplementedError("Skool adapter not yet implemented (Phase 5)")

    async def scrape_profile(self, platform_id):
        raise NotImplementedError("Skool adapter not yet implemented (Phase 5)")

    async def scrape_content(self, platform_id, max_items=20):
        raise NotImplementedError("Skool adapter not yet implemented (Phase 5)")

    async def scrape_pricing(self, platform_id):
        raise NotImplementedError("Skool adapter not yet implemented (Phase 5)")
