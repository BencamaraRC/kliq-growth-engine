"""Instagram platform adapter (Future — stub).

Uses Instagram Graph API. Business/Creator accounts only. 200 calls/hr.
"""

from app.scrapers.base import Platform, PlatformAdapter


class InstagramAdapter(PlatformAdapter):
    @property
    def platform(self) -> Platform:
        return Platform.INSTAGRAM

    async def discover_coaches(self, search_queries, max_results=50):
        raise NotImplementedError("Instagram adapter not yet implemented")

    async def scrape_profile(self, platform_id):
        raise NotImplementedError("Instagram adapter not yet implemented")

    async def scrape_content(self, platform_id, max_items=20):
        raise NotImplementedError("Instagram adapter not yet implemented")

    async def scrape_pricing(self, platform_id):
        raise NotImplementedError("Instagram adapter not yet implemented")
