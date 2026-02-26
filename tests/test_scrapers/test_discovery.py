"""Tests for the discovery orchestrator — dedup and enrichment."""

import pytest

from app.scrapers.base import Platform, ScrapedProfile
from app.scrapers.discovery import (
    DiscoveryOrchestrator,
    EnrichedProspect,
    NAME_SIMILARITY_THRESHOLD,
)


class TestEnrichedProspect:
    def _make_profile(self, name="Coach Mike", platform=Platform.YOUTUBE, **kwargs):
        return ScrapedProfile(platform=platform, platform_id="test123", name=name, **kwargs)

    def test_name_from_primary(self):
        prospect = EnrichedProspect(primary_profile=self._make_profile("Coach Mike"))
        assert prospect.name == "Coach Mike"

    def test_bio_uses_longest(self):
        primary = self._make_profile(bio="Short bio")
        secondary = self._make_profile(platform=Platform.SKOOL, bio="A much longer and more detailed bio about this coach")
        prospect = EnrichedProspect(primary_profile=primary, platform_profiles=[secondary])
        assert "longer" in prospect.bio

    def test_social_links_merged(self):
        primary = self._make_profile(social_links={"instagram": "ig.com/coach"})
        secondary = self._make_profile(
            platform=Platform.SKOOL,
            social_links={"youtube": "yt.com/coach"},
        )
        prospect = EnrichedProspect(primary_profile=primary, platform_profiles=[secondary])
        assert "instagram" in prospect.social_links
        assert "youtube" in prospect.social_links

    def test_total_followers(self):
        primary = self._make_profile(follower_count=1000, subscriber_count=500)
        secondary = self._make_profile(platform=Platform.SKOOL, member_count=200)
        prospect = EnrichedProspect(primary_profile=primary, platform_profiles=[secondary])
        assert prospect.total_followers == 1700

    def test_all_niche_tags(self):
        primary = self._make_profile(niche_tags=["fitness"])
        secondary = self._make_profile(platform=Platform.SKOOL, niche_tags=["yoga", "fitness"])
        prospect = EnrichedProspect(primary_profile=primary, platform_profiles=[secondary])
        assert set(prospect.all_niche_tags) == {"fitness", "yoga"}

    def test_platforms_found_on(self):
        primary = self._make_profile()
        secondary = self._make_profile(platform=Platform.SKOOL)
        prospect = EnrichedProspect(primary_profile=primary, platform_profiles=[secondary])
        assert "youtube" in prospect.platforms_found_on
        assert "skool" in prospect.platforms_found_on

    def test_split_name(self):
        assert DiscoveryOrchestrator._split_name("John Smith") == ("John", "Smith")
        assert DiscoveryOrchestrator._split_name("Madonna") == ("Madonna", None)
        assert DiscoveryOrchestrator._split_name("") == (None, None)
        assert DiscoveryOrchestrator._split_name("John Michael Smith") == ("John", "Michael Smith")


class TestFuzzyNameMatching:
    def test_threshold_constant(self):
        assert 0 < NAME_SIMILARITY_THRESHOLD < 1
        assert NAME_SIMILARITY_THRESHOLD == 0.85
