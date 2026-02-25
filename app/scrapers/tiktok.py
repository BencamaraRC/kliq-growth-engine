"""TikTok platform adapter (Future — stub).

Restricted API, requires approval from TikTok.
"""

from app.scrapers.base import Platform, PlatformAdapter


class TikTokAdapter(PlatformAdapter):
    @property
    def platform(self) -> Platform:
        return Platform.TIKTOK

    async def discover_coaches(self, search_queries, max_results=50):
        raise NotImplementedError("TikTok adapter not yet implemented")

    async def scrape_profile(self, platform_id):
        raise NotImplementedError("TikTok adapter not yet implemented")

    async def scrape_content(self, platform_id, max_items=20):
        raise NotImplementedError("TikTok adapter not yet implemented")

    async def scrape_pricing(self, platform_id):
        raise NotImplementedError("TikTok adapter not yet implemented")
