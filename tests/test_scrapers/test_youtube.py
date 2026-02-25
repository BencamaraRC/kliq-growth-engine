"""Tests for YouTube adapter."""

import pytest

from app.scrapers.base import Platform, ScrapedProfile
from app.scrapers.youtube import YouTubeAdapter


class TestYouTubeAdapter:
    def test_platform_is_youtube(self):
        adapter = YouTubeAdapter(api_key="test-key")
        assert adapter.platform == Platform.YOUTUBE

    def test_extract_niche_tags(self):
        adapter = YouTubeAdapter(api_key="test-key")
        tags = adapter._extract_niche_tags(
            "I'm a fitness coach specializing in yoga and nutrition plans"
        )
        assert "fitness" in tags
        assert "yoga" in tags
        assert "nutrition" in tags

    def test_extract_niche_tags_empty(self):
        adapter = YouTubeAdapter(api_key="test-key")
        tags = adapter._extract_niche_tags("I sell cars and real estate")
        assert len(tags) == 0

    @pytest.mark.asyncio
    async def test_extract_email_from_bio(self):
        adapter = YouTubeAdapter(api_key="test-key")
        profile = ScrapedProfile(
            platform=Platform.YOUTUBE,
            platform_id="test",
            name="Test Coach",
            bio="Contact me at coach@example.com for training",
        )
        email = await adapter.extract_email(profile)
        assert email == "coach@example.com"

    @pytest.mark.asyncio
    async def test_extract_social_links(self):
        adapter = YouTubeAdapter(api_key="test-key")
        text = """
        Follow me on Instagram: instagram.com/fitnesscoach
        My Skool community: skool.com/fitness-elite
        TikTok: tiktok.com/@fitnesscoach
        """
        links = await adapter.extract_social_links(text)
        assert "instagram" in links
        assert "skool" in links
        assert "tiktok" in links
