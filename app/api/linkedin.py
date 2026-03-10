"""LinkedIn outreach API routes."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Prospect
from app.db.session import get_db
from app.outreach.linkedin_service import (
    generate_connection_note,
    get_linkedin_queue,
    get_linkedin_stats,
    update_outreach_status,
)

router = APIRouter()


class ConnectionNoteResponse(BaseModel):
    prospect_id: int
    prospect_name: str
    connection_note: str
    linkedin_url: str
    status: str


class StatusUpdateRequest(BaseModel):
    status: str  # SENT, ACCEPTED, DECLINED, NO_RESPONSE


class LinkedInUrlUpdateRequest(BaseModel):
    linkedin_url: str


class StatusUpdateResponse(BaseModel):
    prospect_id: int
    status: str
    email_triggered: bool


class LinkedInStatsResponse(BaseModel):
    total_with_linkedin: int
    queued: int
    copied: int
    sent: int
    accepted: int
    declined: int
    no_response: int
    accept_rate: float


@router.get("/queue")
async def list_queue(
    status: str | None = Query(default=None, description="Filter by outreach status"),
    limit: int = Query(default=50, le=200),
    db: AsyncSession = Depends(get_db),
):
    """List prospects ready for LinkedIn outreach."""
    return await get_linkedin_queue(db, status_filter=status, limit=limit)


@router.post("/{prospect_id}/copy", response_model=ConnectionNoteResponse)
async def copy_connection_note(
    prospect_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Generate a connection note for a prospect and return it with their LinkedIn URL."""
    try:
        result = await generate_connection_note(db, prospect_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return ConnectionNoteResponse(**result)


@router.patch("/{prospect_id}/status", response_model=StatusUpdateResponse)
async def update_status(
    prospect_id: int,
    body: StatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update LinkedIn outreach status. Triggers ICF email on ACCEPTED."""
    try:
        result = await update_outreach_status(db, prospect_id, body.status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return StatusUpdateResponse(**result)


@router.patch("/{prospect_id}/url")
async def update_linkedin_url(
    prospect_id: int,
    body: LinkedInUrlUpdateRequest,
    db: AsyncSession = Depends(get_db),
):
    """Update a prospect's LinkedIn URL (e.g. after finding their real profile)."""
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    prospect.linkedin_url = body.linkedin_url
    prospect.linkedin_found = True
    await db.commit()
    return {"prospect_id": prospect_id, "linkedin_url": body.linkedin_url}


@router.get("/stats", response_model=LinkedInStatsResponse)
async def stats(db: AsyncSession = Depends(get_db)):
    """Get LinkedIn outreach statistics."""
    return LinkedInStatsResponse(**await get_linkedin_stats(db))
