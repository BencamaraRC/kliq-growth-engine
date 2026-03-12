"""Public blog API endpoints — serves AI-generated blog content."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GeneratedContent, Prospect
from app.db.session import get_db

router = APIRouter()


@router.get("/")
async def list_blogs(db: AsyncSession = Depends(get_db)):
    """List all published blog posts (public, no auth required)."""
    stmt = (
        select(
            GeneratedContent.id,
            GeneratedContent.title,
            GeneratedContent.body,
            GeneratedContent.content_metadata,
            GeneratedContent.generated_at,
            Prospect.name.label("coach_name"),
            Prospect.profile_image_url.label("coach_image"),
        )
        .join(Prospect, GeneratedContent.prospect_id == Prospect.id)
        .where(GeneratedContent.content_type == "blog")
        .order_by(GeneratedContent.generated_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    blogs = []
    for row in rows:
        metadata = row.content_metadata or {}
        body_text = row.body or ""
        excerpt = body_text[:200].strip() + "..." if len(body_text) > 200 else body_text
        blogs.append(
            {
                "id": row.id,
                "title": row.title,
                "excerpt": excerpt,
                "tags": metadata.get("tags", []),
                "seo_title": metadata.get("seo_title", row.title),
                "seo_description": metadata.get("seo_description", excerpt),
                "coach_name": row.coach_name,
                "coach_image": row.coach_image,
                "published_at": row.generated_at.isoformat() if row.generated_at else None,
            }
        )

    return blogs


@router.get("/{blog_id}")
async def get_blog(blog_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single blog post by ID (public, no auth required)."""
    stmt = (
        select(
            GeneratedContent.id,
            GeneratedContent.title,
            GeneratedContent.body,
            GeneratedContent.content_metadata,
            GeneratedContent.generated_at,
            Prospect.name.label("coach_name"),
            Prospect.profile_image_url.label("coach_image"),
        )
        .join(Prospect, GeneratedContent.prospect_id == Prospect.id)
        .where(GeneratedContent.id == blog_id, GeneratedContent.content_type == "blog")
    )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Blog post not found")

    metadata = row.content_metadata or {}
    body_text = row.body or ""
    excerpt = body_text[:200].strip() + "..." if len(body_text) > 200 else body_text

    return {
        "id": row.id,
        "title": row.title,
        "excerpt": excerpt,
        "body_html": body_text,
        "tags": metadata.get("tags", []),
        "seo_title": metadata.get("seo_title", row.title),
        "seo_description": metadata.get("seo_description", excerpt),
        "coach_name": row.coach_name,
        "coach_image": row.coach_image,
        "published_at": row.generated_at.isoformat() if row.generated_at else None,
    }
