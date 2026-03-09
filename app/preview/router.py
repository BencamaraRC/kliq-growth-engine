"""Private store preview route — serves animated preview, gated by claim token."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.preview.app_renderer import render_app_preview
from app.preview.queries import get_generated_content, get_prospect_by_token, get_scraped_thumbnails
from app.preview.renderer import render_store_preview

router = APIRouter()


@router.get("/preview", response_class=HTMLResponse)
async def preview_store(
    token: str = Query(...),
    session: AsyncSession = Depends(get_db),
):
    """Serve the animated store preview for a prospect.

    Private endpoint — requires the prospect's claim_token as a query param.
    """
    prospect = await get_prospect_by_token(session, token)
    if not prospect:
        raise HTTPException(status_code=404, detail="Preview not found")

    generated_content = await get_generated_content(session, prospect["id"])
    if not generated_content:
        raise HTTPException(status_code=404, detail="Preview not available yet")

    claim_url = f"{settings.app_base_url}/claim?token={token}"

    html = render_store_preview(
        prospect=prospect,
        generated_content=generated_content,
        claim_url=claim_url,
    )
    return HTMLResponse(content=html)


@router.get("/app-preview", response_class=HTMLResponse)
async def app_preview_store(
    token: str = Query(...),
    session: AsyncSession = Depends(get_db),
):
    """Serve the animated iOS app preview for a prospect.

    Private endpoint — requires the prospect's claim_token as a query param.
    Used for A/B testing outreach emails (app preview vs webstore preview).
    """
    prospect = await get_prospect_by_token(session, token)
    if not prospect:
        raise HTTPException(status_code=404, detail="Preview not found")

    generated_content = await get_generated_content(session, prospect["id"])
    if not generated_content:
        raise HTTPException(status_code=404, detail="Preview not available yet")

    scraped_thumbs = await get_scraped_thumbnails(session, prospect["id"])

    claim_url = f"{settings.app_base_url}/claim?token={token}"

    html = render_app_preview(
        prospect=prospect,
        generated_content=generated_content,
        claim_url=claim_url,
        scraped_thumbnails=scraped_thumbs,
    )
    return HTMLResponse(content=html)
