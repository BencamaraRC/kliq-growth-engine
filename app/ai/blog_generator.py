"""Generate blog posts from video transcripts.

Takes scraped video content (title, transcript, metadata) and produces
structured blog posts with HTML body, SEO metadata, and tags.
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from app.ai.client import AIClient

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).parent / "prompts"
_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))

# Minimum transcript length to attempt blog generation (chars)
MIN_TRANSCRIPT_LENGTH = 200


@dataclass
class GeneratedBlog:
    blog_title: str
    excerpt: str
    body_html: str
    tags: list[str]
    seo_title: str
    seo_description: str
    source_video_url: str = ""


async def generate_blog(
    client: AIClient,
    coach_name: str,
    title: str,
    transcript: str,
    description: str = "",
    view_count: int = 0,
    video_url: str = "",
) -> GeneratedBlog | None:
    """Generate a single blog post from a video transcript.

    Args:
        client: AIClient instance.
        coach_name: Name of the coach.
        title: Video title.
        transcript: Full video transcript text.
        description: Video description.
        view_count: Number of views.
        video_url: Original video URL.

    Returns:
        GeneratedBlog or None if transcript is too short.
    """
    if len(transcript.strip()) < MIN_TRANSCRIPT_LENGTH:
        logger.info(f"Skipping blog for '{title}' — transcript too short ({len(transcript)} chars)")
        return None

    # Truncate very long transcripts to stay within context limits
    max_transcript = 12000
    if len(transcript) > max_transcript:
        transcript = transcript[:max_transcript] + "\n\n[Transcript truncated]"

    template = _env.get_template("blog_generator.j2")
    prompt = template.render(
        title=title,
        coach_name=coach_name,
        description=description,
        view_count=view_count,
        transcript=transcript,
    )

    result = await client.generate_json(
        prompt=prompt,
        system="You are a content writer for KLIQ, a fitness/wellness creator platform.",
        max_tokens=4096,
    )

    # Handle null response for empty/bad transcripts
    if not result.get("body_html"):
        logger.info(f"Blog generation returned null for '{title}'")
        return None

    logger.info(f"Generated blog: '{result.get('blog_title', title)}'")

    return GeneratedBlog(
        blog_title=result.get("blog_title", title),
        excerpt=result.get("excerpt", ""),
        body_html=result.get("body_html", ""),
        tags=result.get("tags", []),
        seo_title=result.get("seo_title", ""),
        seo_description=result.get("seo_description", ""),
        source_video_url=video_url,
    )


async def generate_blogs_batch(
    client: AIClient,
    coach_name: str,
    videos: list[dict],
    max_blogs: int = 5,
) -> list[GeneratedBlog]:
    """Generate blog posts from a batch of videos.

    Selects the best videos (by view count) and generates blogs for each.

    Args:
        client: AIClient instance.
        coach_name: Coach's name.
        videos: List of dicts with keys: title, transcript, description, view_count, url.
        max_blogs: Maximum number of blogs to generate.

    Returns:
        List of generated blogs.
    """
    # Filter videos with usable transcripts and sort by views
    eligible = [
        v for v in videos
        if v.get("transcript", "") and len(v.get("transcript", "")) >= MIN_TRANSCRIPT_LENGTH
    ]
    eligible.sort(key=lambda v: v.get("view_count", 0), reverse=True)

    blogs = []
    for video in eligible[:max_blogs]:
        blog = await generate_blog(
            client=client,
            coach_name=coach_name,
            title=video.get("title", ""),
            transcript=video.get("transcript", ""),
            description=video.get("description", ""),
            view_count=video.get("view_count", 0),
            video_url=video.get("url", ""),
        )
        if blog:
            blogs.append(blog)

    logger.info(f"Generated {len(blogs)} blogs for {coach_name} from {len(eligible)} eligible videos")
    return blogs
