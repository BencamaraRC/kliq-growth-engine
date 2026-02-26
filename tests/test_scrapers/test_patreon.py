"""Tests for Patreon adapter helpers."""

from app.scrapers.base import Platform
from app.scrapers.patreon import PatreonAdapter, _extract_patreon_slug, _parse_patreon_price


class TestPatreonAdapter:
    def test_platform_is_patreon(self):
        adapter = PatreonAdapter()
        assert adapter.platform == Platform.PATREON

    def test_niche_tag_extraction(self):
        tags = PatreonAdapter._extract_niche_tags("Yoga and meditation teacher")
        assert "yoga" in tags

    def test_niche_tags_empty(self):
        tags = PatreonAdapter._extract_niche_tags("")
        assert tags == []


class TestExtractSlug:
    def test_full_url(self):
        assert _extract_patreon_slug("https://www.patreon.com/fitnesscoach") == "fitnesscoach"

    def test_url_with_c(self):
        assert _extract_patreon_slug("https://patreon.com/c/yoga_master") == "yoga_master"

    def test_relative_path(self):
        assert _extract_patreon_slug("/fitnesscoach") == "fitnesscoach"

    def test_filtered_slugs(self):
        assert _extract_patreon_slug("/posts") is None
        assert _extract_patreon_slug("/login") is None
        assert _extract_patreon_slug("/about") is None

    def test_empty(self):
        assert _extract_patreon_slug("") is None

    def test_none(self):
        assert _extract_patreon_slug(None) is None


class TestParsePrice:
    def test_dollar_amount(self):
        assert _parse_patreon_price("$5 per month") == 5.0

    def test_pound_amount(self):
        assert _parse_patreon_price("£10.99/month") == 10.99

    def test_empty(self):
        assert _parse_patreon_price("") == 0.0

    def test_no_currency(self):
        assert _parse_patreon_price("Free") == 0.0
