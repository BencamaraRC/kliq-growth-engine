"""Discovery orchestrator — coordinates scraping across all platform adapters.

Handles cross-platform enrichment (e.g., YouTube channel links to Skool/Patreon)
and deduplication of coaches found on multiple platforms.
"""

import logging
from dataclasses import dataclass, field

from app.scrapers.base import (
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)

logger = logging.getLogger(__name__)


@dataclass
class EnrichedProspect:
    """A coach enriched with data from multiple platforms."""

    primary_profile: ScrapedProfile
    platform_profiles: list[ScrapedProfile] = field(default_factory=list)
    all_content: list[ScrapedContent] = field(default_factory=list)
    all_pricing: list[ScrapedPricing] = field(default_factory=list)
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    @property
    def name(self) -> str:
        return self.primary_profile.name

    @property
    def bio(self) -> str:
        return self.primary_profile.bio

    @property
    def profile_image_url(self) -> str:
        return self.primary_profile.profile_image_url

    @property
    def social_links(self) -> dict:
        merged = {}
        for profile in [self.primary_profile] + self.platform_profiles:
            merged.update(profile.social_links)
        return merged

    @property
    def brand_colors(self) -> list[str]:
        for profile in [self.primary_profile] + self.platform_profiles:
            if profile.brand_colors:
                return profile.brand_colors
        return []


class DiscoveryOrchestrator:
    """Coordinates discovery across all platform adapters.

    Deduplicates coaches found on multiple platforms and enriches
    profiles by following cross-platform links.
    """

    def __init__(self, adapters: list[PlatformAdapter]):
        self.adapters = {a.platform: a for a in adapters}

    async def discover(
        self,
        search_queries: list[str],
        platforms: list[str] | None = None,
        max_per_platform: int = 50,
    ) -> list[EnrichedProspect]:
        """Run discovery across all (or specified) adapters.

        Args:
            search_queries: Search terms for finding coaches.
            platforms: Platform names to search (None = all registered).
            max_per_platform: Maximum results per platform.

        Returns:
            List of deduplicated, enriched prospects.
        """
        target_adapters = (
            {k: v for k, v in self.adapters.items() if k.value in platforms}
            if platforms
            else self.adapters
        )

        all_profiles: list[ScrapedProfile] = []

        for platform, adapter in target_adapters.items():
            try:
                logger.info(f"Discovering coaches on {platform.value}...")
                profiles = await adapter.discover_coaches(
                    search_queries, max_results=max_per_platform
                )
                all_profiles.extend(profiles)
                logger.info(f"Found {len(profiles)} coaches on {platform.value}")
            except Exception as e:
                logger.error(f"Discovery failed on {platform.value}: {e}")
                continue

        # Deduplicate and enrich
        prospects = await self._deduplicate_and_enrich(all_profiles)
        return prospects

    async def scrape_single(self, platform: str, platform_id: str) -> EnrichedProspect:
        """Scrape a single coach from a specific platform and enrich."""
        adapter = self.adapters.get(platform)
        if not adapter:
            raise ValueError(f"No adapter registered for platform: {platform}")

        profile = await adapter.scrape_profile(platform_id)
        content = await adapter.scrape_content(platform_id)
        pricing = await adapter.scrape_pricing(platform_id)

        email = profile.email or await adapter.extract_email(profile)
        first_name, last_name = self._split_name(profile.name)

        prospect = EnrichedProspect(
            primary_profile=profile,
            all_content=content,
            all_pricing=pricing,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        # Follow cross-platform links
        prospect = await self._cross_platform_enrich(prospect)

        return prospect

    async def _deduplicate_and_enrich(
        self, profiles: list[ScrapedProfile]
    ) -> list[EnrichedProspect]:
        """Deduplicate profiles by email or name similarity."""
        prospects: list[EnrichedProspect] = []
        seen_emails: set[str] = set()
        seen_names: set[str] = set()

        for profile in profiles:
            email = profile.email
            name_key = profile.name.lower().strip()

            # Skip if already seen by email
            if email and email in seen_emails:
                continue

            # Skip if already seen by name (simple dedup)
            if name_key in seen_names:
                continue

            if email:
                seen_emails.add(email)
            seen_names.add(name_key)

            first_name, last_name = self._split_name(profile.name)

            prospects.append(
                EnrichedProspect(
                    primary_profile=profile,
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                )
            )

        return prospects

    async def _cross_platform_enrich(
        self, prospect: EnrichedProspect
    ) -> EnrichedProspect:
        """Follow social links to enrich profile from other platforms.

        If a YouTube channel links to Skool/Patreon/website, scrape those too.
        """
        social = prospect.social_links

        for platform_name, link in social.items():
            adapter = self.adapters.get(platform_name)
            if adapter is None:
                continue

            try:
                # Extract platform ID from the link
                platform_id = link.split("/")[-1].lstrip("@")
                profile = await adapter.scrape_profile(platform_id)
                content = await adapter.scrape_content(platform_id)
                pricing = await adapter.scrape_pricing(platform_id)

                prospect.platform_profiles.append(profile)
                prospect.all_content.extend(content)
                prospect.all_pricing.extend(pricing)

                # Update email if found on another platform
                if not prospect.email and profile.email:
                    prospect.email = profile.email

                logger.info(
                    f"Cross-platform enriched {prospect.name} from {platform_name}"
                )
            except Exception as e:
                logger.debug(f"Cross-platform enrichment failed for {platform_name}: {e}")
                continue

        return prospect

    @staticmethod
    def _split_name(name: str) -> tuple[str | None, str | None]:
        """Split a display name into first/last name."""
        parts = name.strip().split(None, 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        elif len(parts) == 1:
            return parts[0], None
        return None, None
