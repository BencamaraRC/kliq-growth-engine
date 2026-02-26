"""Discovery orchestrator — coordinates scraping across all platform adapters.

Handles:
- Multi-platform discovery (run adapters in parallel where possible)
- Cross-platform enrichment (YouTube → Skool/Patreon/website chain)
- Deduplication by email, URL, and fuzzy name matching
- Priority ordering (profiles with email first, higher followers first)
"""

import logging
from dataclasses import dataclass, field
from difflib import SequenceMatcher

from app.scrapers.base import (
    Platform,
    PlatformAdapter,
    ScrapedContent,
    ScrapedPricing,
    ScrapedProfile,
)

logger = logging.getLogger(__name__)

# Fuzzy name match threshold (0-1). 0.85 = fairly strict
NAME_SIMILARITY_THRESHOLD = 0.85


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
        # Use the longest bio across all platforms
        bios = [self.primary_profile.bio] + [p.bio for p in self.platform_profiles]
        return max(bios, key=len) if bios else ""

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

    @property
    def total_followers(self) -> int:
        """Sum followers across all platforms."""
        total = self.primary_profile.follower_count + self.primary_profile.subscriber_count
        for p in self.platform_profiles:
            total += p.follower_count + p.subscriber_count + p.member_count
        return total

    @property
    def all_niche_tags(self) -> list[str]:
        """Merge niche tags from all platforms."""
        tags = set(self.primary_profile.niche_tags)
        for p in self.platform_profiles:
            tags.update(p.niche_tags)
        return sorted(tags)

    @property
    def platforms_found_on(self) -> list[str]:
        """List of platforms this coach was found on."""
        platforms = [self.primary_profile.platform.value]
        for p in self.platform_profiles:
            if p.platform.value not in platforms:
                platforms.append(p.platform.value)
        return platforms


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
            List of deduplicated, enriched prospects sorted by quality.
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
            except NotImplementedError:
                logger.debug(f"Adapter {platform.value} not yet implemented, skipping")
            except Exception as e:
                logger.error(f"Discovery failed on {platform.value}: {e}")
                continue

        # Deduplicate and enrich
        prospects = await self._deduplicate_and_enrich(all_profiles)

        # Sort by quality: email first, then by follower count
        prospects.sort(
            key=lambda p: (p.email is not None, p.total_followers),
            reverse=True,
        )

        return prospects

    async def scrape_single(self, platform: str, platform_id: str) -> EnrichedProspect:
        """Scrape a single coach from a specific platform and enrich."""
        # Accept both Platform enum and string
        adapter = None
        for p, a in self.adapters.items():
            if p == platform or p.value == platform:
                adapter = a
                break

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
        """Deduplicate profiles by email, URL, or fuzzy name matching."""
        prospects: list[EnrichedProspect] = []
        seen_emails: set[str] = set()
        seen_urls: set[str] = set()

        for profile in profiles:
            email = profile.email
            url_key = profile.website_url or ""

            # Skip if already seen by email
            if email and email.lower() in seen_emails:
                # Merge into existing prospect
                self._merge_into_existing(prospects, profile, by="email", value=email.lower())
                continue

            # Skip if already seen by website URL
            if url_key and url_key.lower() in seen_urls:
                self._merge_into_existing(prospects, profile, by="url", value=url_key.lower())
                continue

            # Fuzzy name dedup
            name_key = profile.name.lower().strip()
            existing = self._find_fuzzy_name_match(prospects, name_key)
            if existing:
                existing.platform_profiles.append(profile)
                if email and not existing.email:
                    existing.email = email
                continue

            if email:
                seen_emails.add(email.lower())
            if url_key:
                seen_urls.add(url_key.lower())

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

    def _merge_into_existing(
        self,
        prospects: list[EnrichedProspect],
        profile: ScrapedProfile,
        by: str,
        value: str,
    ):
        """Merge a duplicate profile into an existing prospect."""
        for prospect in prospects:
            if by == "email" and prospect.email and prospect.email.lower() == value:
                prospect.platform_profiles.append(profile)
                return
            if by == "url":
                urls = [prospect.primary_profile.website_url or ""]
                urls += [p.website_url or "" for p in prospect.platform_profiles]
                if any(u.lower() == value for u in urls if u):
                    prospect.platform_profiles.append(profile)
                    return

    def _find_fuzzy_name_match(
        self,
        prospects: list[EnrichedProspect],
        name: str,
    ) -> EnrichedProspect | None:
        """Find an existing prospect with a similar name."""
        for prospect in prospects:
            existing_name = prospect.name.lower().strip()
            ratio = SequenceMatcher(None, name, existing_name).ratio()
            if ratio >= NAME_SIMILARITY_THRESHOLD:
                return prospect
        return None

    async def _cross_platform_enrich(
        self, prospect: EnrichedProspect
    ) -> EnrichedProspect:
        """Follow social links to enrich profile from other platforms.

        If a YouTube channel links to Skool/Patreon/website, scrape those too.
        """
        social = prospect.social_links

        for platform_name, link in social.items():
            # Find adapter by platform name string
            adapter = None
            for p, a in self.adapters.items():
                if p.value == platform_name:
                    adapter = a
                    break

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
            except NotImplementedError:
                logger.debug(f"{platform_name} adapter not yet implemented, skipping enrichment")
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
