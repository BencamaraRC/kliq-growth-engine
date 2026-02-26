"""Tests for Website adapter helpers."""

from bs4 import BeautifulSoup

from app.scrapers.base import Platform
from app.scrapers.website import (
    WebsiteAdapter,
    _extract_email,
    _extract_social_links_from_soup,
    _normalize_url,
    _og_content,
    _meta_content,
)


class TestWebsiteAdapter:
    def test_platform_is_website(self):
        adapter = WebsiteAdapter()
        assert adapter.platform == Platform.WEBSITE

    def test_niche_tag_extraction(self):
        tags = WebsiteAdapter._extract_niche_tags("Personal fitness coaching and nutrition plans")
        assert "fitness" in tags
        assert "nutrition" in tags
        assert "coaching" in tags


class TestNormalizeUrl:
    def test_adds_https(self):
        assert _normalize_url("example.com") == "https://example.com"

    def test_keeps_existing_https(self):
        assert _normalize_url("https://example.com") == "https://example.com"

    def test_keeps_existing_http(self):
        assert _normalize_url("http://example.com") == "http://example.com"


class TestExtractEmail:
    def test_finds_email(self):
        assert _extract_email("Contact me at coach@fitness.com for inquiries") == "coach@fitness.com"

    def test_no_email(self):
        assert _extract_email("No contact info here") is None


class TestOGContent:
    def test_extracts_og_title(self):
        html = '<html><head><meta property="og:title" content="Coach Mike"></head></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert _og_content(soup, "og:title") == "Coach Mike"

    def test_missing_og(self):
        html = "<html><head></head></html>"
        soup = BeautifulSoup(html, "html.parser")
        assert _og_content(soup, "og:title") == ""


class TestMetaContent:
    def test_extracts_description(self):
        html = '<html><head><meta name="description" content="Fitness coaching site"></head></html>'
        soup = BeautifulSoup(html, "html.parser")
        assert _meta_content(soup, "description") == "Fitness coaching site"


class TestSocialLinkExtraction:
    def test_extracts_instagram(self):
        html = '<html><body><a href="https://instagram.com/coachfit">IG</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = _extract_social_links_from_soup(soup)
        assert "instagram" in links

    def test_extracts_youtube(self):
        html = '<html><body><a href="https://youtube.com/@coachfit">YT</a></body></html>'
        soup = BeautifulSoup(html, "html.parser")
        links = _extract_social_links_from_soup(soup)
        assert "youtube" in links

    def test_extracts_multiple(self):
        html = """<html><body>
            <a href="https://instagram.com/coach">IG</a>
            <a href="https://tiktok.com/@coach">TT</a>
            <a href="https://skool.com/fitness-hub">Skool</a>
        </body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        links = _extract_social_links_from_soup(soup)
        assert len(links) == 3
        assert "instagram" in links
        assert "tiktok" in links
        assert "skool" in links
