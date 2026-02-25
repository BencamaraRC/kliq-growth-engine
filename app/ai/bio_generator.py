"""Generate coach bios from scraped profile data.

Takes a ScrapedProfile (+ optional content titles) and produces a
structured bio suitable for a KLIQ webstore About page.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.ai.client import AIClient

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


@dataclass
class GeneratedBio:
    tagline: str
    short_bio: str
    long_bio: str
    specialties: list[str]
    coaching_style: str


async def generate_bio(
    client: AIClient,
    name: str,
    platform: str,
    bio: str = "",
    niche_tags: list[str] | None = None,
    follower_count: int = 0,
    content_count: int = 0,
    content_titles: list[str] | None = None,
) -> GeneratedBio:
    """Generate a polished coach bio for their KLIQ store.

    Args:
        client: AIClient instance.
        name: Coach's display name.
        platform: Source platform (e.g., "youtube").
        bio: Original bio text from the platform.
        niche_tags: Detected niche categories.
        follower_count: Number of followers/subscribers.
        content_count: Number of content pieces.
        content_titles: Titles of recent content for context.

    Returns:
        GeneratedBio with tagline, short/long bio, specialties, and coaching style.
    """
    template = _env.get_template("bio_generator.j2")
    prompt = template.render(
        name=name,
        platform=platform,
        bio=bio,
        niche_tags=niche_tags or [],
        follower_count=follower_count,
        content_count=content_count,
        content_titles=content_titles or [],
    )

    result = await client.generate_json(
        prompt=prompt,
        system="You are a professional copywriter for KLIQ, a fitness/wellness creator platform.",
    )

    logger.info(f"Generated bio for {name}: tagline='{result.get('tagline', '')}'")

    return GeneratedBio(
        tagline=result.get("tagline", f"{name} — Fitness & Wellness"),
        short_bio=result.get("short_bio", ""),
        long_bio=result.get("long_bio", ""),
        specialties=result.get("specialties", []),
        coaching_style=result.get("coaching_style", ""),
    )
