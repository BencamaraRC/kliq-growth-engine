"""Brand color extraction from images.

Uses ColorThief to extract dominant colors from a coach's profile image
or banner. Maps extracted colors to the KLIQ ApplicationColor schema
(30+ color fields — primary, secondary, accent, backgrounds, etc.).
"""

import logging
from dataclasses import dataclass, field
from io import BytesIO

import httpx
from colorthief import ColorThief
from PIL import Image

logger = logging.getLogger(__name__)


@dataclass
class BrandColors:
    """Extracted brand colors mapped to KLIQ store theming."""

    primary: str  # Main brand color (hex)
    secondary: str  # Secondary accent (hex)
    accent: str  # Highlight color (hex)
    background: str = "#FFFFFF"
    text: str = "#1A1A1A"
    palette: list[str] = field(default_factory=list)  # Full extracted palette


async def extract_colors_from_url(image_url: str, color_count: int = 6) -> BrandColors | None:
    """Download an image and extract brand colors.

    Args:
        image_url: URL of the image to analyze.
        color_count: Number of palette colors to extract.

    Returns:
        BrandColors or None if extraction fails.
    """
    if not image_url:
        return None

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(image_url)
            response.raise_for_status()

        return extract_colors_from_bytes(response.content, color_count)

    except Exception as e:
        logger.warning(f"Failed to download image for color extraction: {e}")
        return None


def extract_colors_from_bytes(image_bytes: bytes, color_count: int = 6) -> BrandColors | None:
    """Extract brand colors from image bytes.

    Args:
        image_bytes: Raw image data.
        color_count: Number of palette colors to extract.

    Returns:
        BrandColors or None if extraction fails.
    """
    try:
        # Resize image for faster processing
        img = Image.open(BytesIO(image_bytes))
        img.thumbnail((200, 200))

        buf = BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)

        ct = ColorThief(buf)

        # Get dominant color
        dominant = ct.get_color(quality=1)

        # Get palette
        palette = ct.get_palette(color_count=color_count, quality=1)

        hex_palette = [_rgb_to_hex(c) for c in palette]
        dominant_hex = _rgb_to_hex(dominant)

        # Assign roles: primary = dominant, secondary = 2nd, accent = 3rd
        primary = dominant_hex
        secondary = hex_palette[1] if len(hex_palette) > 1 else _darken(primary, 0.2)
        accent = hex_palette[2] if len(hex_palette) > 2 else _lighten(primary, 0.3)

        # Determine text color based on primary brightness
        text = "#FFFFFF" if _is_dark(dominant) else "#1A1A1A"
        background = "#FFFFFF" if _is_dark(dominant) else "#F9FAFB"

        return BrandColors(
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text=text,
            palette=hex_palette,
        )

    except Exception as e:
        logger.warning(f"Color extraction failed: {e}")
        return None


def _rgb_to_hex(rgb: tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex string."""
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Convert hex string to RGB tuple."""
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _is_dark(rgb: tuple[int, int, int]) -> bool:
    """Check if a color is dark (luminance < 128)."""
    luminance = 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]
    return luminance < 128


def _darken(hex_color: str, factor: float) -> str:
    """Darken a color by a factor (0-1)."""
    r, g, b = _hex_to_rgb(hex_color)
    r = max(0, int(r * (1 - factor)))
    g = max(0, int(g * (1 - factor)))
    b = max(0, int(b * (1 - factor)))
    return _rgb_to_hex((r, g, b))


def _lighten(hex_color: str, factor: float) -> str:
    """Lighten a color by a factor (0-1)."""
    r, g, b = _hex_to_rgb(hex_color)
    r = min(255, int(r + (255 - r) * factor))
    g = min(255, int(g + (255 - g) * factor))
    b = min(255, int(b + (255 - b) * factor))
    return _rgb_to_hex((r, g, b))
