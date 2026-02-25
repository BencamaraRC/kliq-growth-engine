"""Generate SEO metadata for a coach's KLIQ webstore.

Produces page titles, meta descriptions, keywords, Open Graph data,
and a URL-friendly store slug.
"""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.ai.client import AIClient

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


@dataclass
class GeneratedSEO:
    seo_title: str
    seo_description: str
    seo_keywords: list[str] = field(default_factory=list)
    og_title: str = ""
    og_description: str = ""
    store_slug: str = ""


async def generate_seo(
    client: AIClient,
    name: str,
    store_name: str | None = None,
    tagline: str = "",
    specialties: list[str] | None = None,
    niche_tags: list[str] | None = None,
    location: str = "",
    content_titles: list[str] | None = None,
) -> GeneratedSEO:
    """Generate SEO metadata for a KLIQ store.

    Args:
        client: AIClient instance.
        name: Coach's name.
        store_name: Store display name (defaults to coach name).
        tagline: Coach tagline (from bio generator).
        specialties: Coach specialties (from bio generator).
        niche_tags: Detected niche tags.
        location: Coach's location if known.
        content_titles: Titles of store content for keyword context.

    Returns:
        GeneratedSEO with all metadata fields.
    """
    store_name = store_name or name

    template = _env.get_template("seo_generator.j2")
    prompt = template.render(
        name=name,
        store_name=store_name,
        tagline=tagline,
        specialties=specialties or [],
        niche_tags=niche_tags or [],
        location=location,
        content_titles=content_titles or [],
    )

    result = await client.generate_json(
        prompt=prompt,
        system="You are an SEO specialist for KLIQ, a fitness/wellness creator platform.",
    )

    # Validate and sanitize the slug
    slug = result.get("store_slug", "")
    if not slug:
        slug = _generate_slug(name)
    slug = _sanitize_slug(slug)

    logger.info(f"Generated SEO for {name}: slug='{slug}'")

    return GeneratedSEO(
        seo_title=result.get("seo_title", f"{name} | KLIQ")[:60],
        seo_description=result.get("seo_description", "")[:155],
        seo_keywords=result.get("seo_keywords", [])[:12],
        og_title=result.get("og_title", result.get("seo_title", name))[:60],
        og_description=result.get("og_description", result.get("seo_description", ""))[:200],
        store_slug=slug,
    )


def _generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a name."""
    return _sanitize_slug(name.lower())


def _sanitize_slug(slug: str) -> str:
    """Ensure slug is URL-safe: lowercase, hyphens, no special chars."""
    slug = slug.lower().strip()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    return slug.strip("-")[:50]
