"""Private store preview route — serves animated preview, gated by claim token."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.preview.queries import get_generated_content, get_prospect_by_token
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

    html = render_store_preview(
        prospect=prospect,
        generated_content=generated_content,
    )
    return HTMLResponse(content=html)
