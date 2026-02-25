"""Tests for the color extractor utilities."""

from app.scrapers.color_extractor import (
    _darken,
    _hex_to_rgb,
    _is_dark,
    _lighten,
    _rgb_to_hex,
)


class TestColorUtils:
    def test_rgb_to_hex(self):
        assert _rgb_to_hex((255, 0, 0)) == "#ff0000"
        assert _rgb_to_hex((0, 128, 255)) == "#0080ff"
        assert _rgb_to_hex((0, 0, 0)) == "#000000"

    def test_hex_to_rgb(self):
        assert _hex_to_rgb("#ff0000") == (255, 0, 0)
        assert _hex_to_rgb("#000000") == (0, 0, 0)
        assert _hex_to_rgb("ffffff") == (255, 255, 255)

    def test_is_dark(self):
        assert _is_dark((0, 0, 0)) is True
        assert _is_dark((255, 255, 255)) is False
        assert _is_dark((50, 50, 50)) is True
        assert _is_dark((200, 200, 200)) is False

    def test_darken(self):
        result = _darken("#ff0000", 0.5)
        assert result == "#7f0000"  # int(255 * 0.5) = 127 = 0x7f

    def test_lighten(self):
        result = _lighten("#000000", 0.5)
        assert result == "#7f7f7f"  # int(255 * 0.5) = 127 = 0x7f

    def test_lighten_white_stays_white(self):
        result = _lighten("#ffffff", 0.5)
        assert result == "#ffffff"
