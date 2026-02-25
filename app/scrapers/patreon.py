"""Patreon platform adapter (Phase 5 — stub).

Will use Patreon API v2 with OAuth 2.0.
"""

from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)


class PatreonAdapter(PlatformAdapter):
    @property
    def platform(self) -> Platform:
        return Platform.PATREON

    async def discover_coaches(self, search_queries, max_results=50):
        raise NotImplementedError("Patreon adapter not yet implemented (Phase 5)")

    async def scrape_profile(self, platform_id):
        raise NotImplementedError("Patreon adapter not yet implemented (Phase 5)")

    async def scrape_content(self, platform_id, max_items=20):
        raise NotImplementedError("Patreon adapter not yet implemented (Phase 5)")

    async def scrape_pricing(self, platform_id):
        raise NotImplementedError("Patreon adapter not yet implemented (Phase 5)")
