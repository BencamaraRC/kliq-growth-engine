"""Public store preview route — serves animated preview as a standalone web page."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.session import get_db
from app.preview.queries import get_generated_content, get_prospect_by_id
from app.preview.renderer import render_store_preview

router = APIRouter()


@router.get("/preview/{prospect_id}", response_class=HTMLResponse)
async def preview_store(prospect_id: int, session: AsyncSession = Depends(get_db)):
    """Serve the animated store preview for a prospect.

    Public endpoint — no auth required. Linked from outreach emails so
    prospects can see what their KLIQ store looks like before claiming.
    """
    prospect = await get_prospect_by_id(session, prospect_id)
    if not prospect:
        raise HTTPException(status_code=404, detail="Preview not found")

    generated_content = await get_generated_content(session, prospect_id)
    if not generated_content:
        raise HTTPException(status_code=404, detail="Preview not available yet")

    # Build claim CTA URL
    claim_cta_url = None
    if prospect.get("claim_token"):
        claim_cta_url = f"{settings.claim_base_url}?token={prospect['claim_token']}"

    html = render_store_preview(
        prospect=prospect,
        generated_content=generated_content,
        claim_cta_url=claim_cta_url,
    )
    return HTMLResponse(content=html)
