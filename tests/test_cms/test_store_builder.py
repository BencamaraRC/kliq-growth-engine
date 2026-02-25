"""Tests for the CMS store builder — color mapping and helper functions."""

import pytest

from app.cms.store_builder import _build_colors, _is_dark_hex
from app.scrapers.color_extractor import BrandColors


class TestColorMapping:
    """Test mapping of extracted brand colors to CMS ApplicationColor."""

    def test_default_colors_when_no_brand(self):
        """When no brand colors provided, use CMS defaults."""
        colors = _build_colors(app_id=999, brand_colors=None)
        assert colors.application_id == 999
        assert colors.primary == "1E81FF"
        assert colors.on_primary == "FFFFFF"
        assert colors.secondary == "1A74E5"
        assert colors.button_primary == "1E81FF"

    def test_brand_colors_applied(self):
        """When brand colors provided, they override defaults."""
        brand = BrandColors(
            primary="#FF5733",
            secondary="#33FF57",
            accent="#3357FF",
            background="#FAFAFA",
            text="#222222",
        )
        colors = _build_colors(app_id=100, brand_colors=brand)
        assert colors.primary == "FF5733"
        assert colors.secondary == "33FF57"
        assert colors.button_primary == "FF5733"
        assert colors.background == "FAFAFA"

    def test_hex_stripped_of_hash(self):
        """CMS stores colors without # prefix."""
        brand = BrandColors(
            primary="#AABBCC",
            secondary="#112233",
            accent="#445566",
        )
        colors = _build_colors(app_id=1, brand_colors=brand)
        assert "#" not in colors.primary
        assert "#" not in colors.secondary

    def test_on_colors_contrast(self):
        """Dark primary → white text on top; light primary → dark text."""
        dark_brand = BrandColors(primary="#1A1A1A", secondary="#333333", accent="#555555")
        colors = _build_colors(app_id=1, brand_colors=dark_brand)
        assert colors.on_primary == "FFFFFF"

        light_brand = BrandColors(primary="#EEEEEE", secondary="#DDDDDD", accent="#CCCCCC")
        colors = _build_colors(app_id=1, brand_colors=light_brand)
        assert colors.on_primary == "1A1A1A"


class TestIsDarkHex:
    def test_black_is_dark(self):
        assert _is_dark_hex("000000") is True

    def test_white_is_not_dark(self):
        assert _is_dark_hex("FFFFFF") is False

    def test_blue_primary_is_dark(self):
        # KLIQ blue 1E81FF: luminance = 0.299*30 + 0.587*129 + 0.114*255 ≈ 113.8 < 128
        assert _is_dark_hex("1E81FF") is True

    def test_invalid_hex_returns_false(self):
        assert _is_dark_hex("xyz") is False
