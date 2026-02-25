"""Create pages (blog posts, about page) in the CMS from AI-generated content."""

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.blog_generator import GeneratedBlog
from app.cms.models import Page
from app.cms.store_builder import STATUS_INACTIVE, SUPER_ADMIN_ID

logger = logging.getLogger(__name__)

# CMS page_type_id values (from page_types table)
PAGE_TYPE_ABOUT = 1
PAGE_TYPE_BLOG = 2


async def create_about_page(
    session: AsyncSession,
    application_id: int,
    long_bio: str,
    tagline: str = "",
    profile_image_url: str | None = None,
) -> int:
    """Create an About page for the coach's store.

    Args:
        session: CMS MySQL session.
        application_id: The CMS application ID.
        long_bio: AI-generated long bio (HTML).
        tagline: Coach tagline for the page title.
        profile_image_url: Profile image for the page.

    Returns:
        Created page ID.
    """
    page = Page(
        application_id=application_id,
        title=tagline or "About",
        description=long_bio,
        page_type_id=PAGE_TYPE_ABOUT,
        media_url=profile_image_url,
        order=0,
        status_id=STATUS_INACTIVE,
        created_by=SUPER_ADMIN_ID,
        updated_by=SUPER_ADMIN_ID,
    )
    session.add(page)
    await session.flush()

    logger.info(f"Created About page for app {application_id}")
    return page.id


async def create_blog_pages(
    session: AsyncSession,
    application_id: int,
    blogs: list[GeneratedBlog],
) -> list[int]:
    """Create blog post pages from AI-generated blogs.

    Args:
        session: CMS MySQL session.
        application_id: The CMS application ID.
        blogs: List of AI-generated blog posts.

    Returns:
        List of created page IDs.
    """
    page_ids = []

    for order, blog in enumerate(blogs):
        page = Page(
            application_id=application_id,
            title=blog.blog_title[:255] if blog.blog_title else "Blog Post",
            description=blog.body_html,
            page_type_id=PAGE_TYPE_BLOG,
            order=order + 1,  # After the About page
            status_id=STATUS_INACTIVE,
            meta_title=blog.seo_title[:255] if blog.seo_title else None,
            meta_description=blog.seo_description,
            created_by=SUPER_ADMIN_ID,
            updated_by=SUPER_ADMIN_ID,
        )
        session.add(page)
        await session.flush()
        page_ids.append(page.id)

        logger.info(f"Created blog page '{blog.blog_title}' for app {application_id}")

    return page_ids
