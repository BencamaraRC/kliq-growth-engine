"""Tests for SEO generator utility functions."""

from app.ai.seo_generator import _generate_slug, _sanitize_slug


class TestSlugGeneration:
    def test_basic_slug(self):
        assert _generate_slug("John Smith") == "john-smith"

    def test_slug_special_chars(self):
        assert _sanitize_slug("Coach Mike's Fitness!") == "coach-mikes-fitness"

    def test_slug_multiple_spaces(self):
        assert _sanitize_slug("Coach   Mike   Fit") == "coach-mike-fit"

    def test_slug_max_length(self):
        long_name = "a" * 100
        result = _sanitize_slug(long_name)
        assert len(result) <= 50

    def test_slug_strips_leading_trailing_hyphens(self):
        assert _sanitize_slug("--test--") == "test"

    def test_slug_empty_string(self):
        assert _sanitize_slug("") == ""
