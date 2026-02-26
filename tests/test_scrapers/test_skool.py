"""Tests for Skool adapter helpers."""

from app.scrapers.base import Platform
from app.scrapers.skool import SkoolAdapter, _parse_number, _parse_price


class TestSkoolAdapter:
    def test_platform_is_skool(self):
        adapter = SkoolAdapter()
        assert adapter.platform == Platform.SKOOL

    def test_niche_tag_extraction(self):
        tags = SkoolAdapter._extract_niche_tags("Online fitness coaching community for weight loss")
        assert "fitness" in tags
        assert "coaching" in tags
        assert "weight_loss" in tags

    def test_niche_tags_empty(self):
        tags = SkoolAdapter._extract_niche_tags("")
        assert tags == []


class TestParseNumber:
    def test_plain_number(self):
        assert _parse_number("1234") == 1234

    def test_number_with_k(self):
        assert _parse_number("12.5K members") == 12500

    def test_number_with_m(self):
        assert _parse_number("1.2M") == 1200000

    def test_comma_separated(self):
        assert _parse_number("1,234") == 1234

    def test_empty(self):
        assert _parse_number("") == 0

    def test_no_number(self):
        assert _parse_number("members") == 0


class TestParsePrice:
    def test_usd_monthly(self):
        result = _parse_price("$29/month")
        assert result["amount"] == 29.0
        assert result["currency"] == "USD"
        assert result["interval"] == "month"

    def test_gbp_yearly(self):
        result = _parse_price("£49.99/year")
        assert result["amount"] == 49.99
        assert result["currency"] == "GBP"
        assert result["interval"] == "year"

    def test_empty(self):
        result = _parse_price("")
        assert result["amount"] == 0
