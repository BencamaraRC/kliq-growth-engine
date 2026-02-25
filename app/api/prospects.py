"""Prospect API routes — CRUD and discovery triggers."""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Platform, Prospect, ProspectStatus
from app.db.session import get_db

router = APIRouter()


class ProspectResponse(BaseModel):
    id: int
    name: str
    email: str | None
    status: str
    primary_platform: str
    primary_platform_id: str
    follower_count: int
    subscriber_count: int
    niche_tags: list | None
    kliq_application_id: int | None
    kliq_store_url: str | None

    model_config = {"from_attributes": True}


class ProspectListResponse(BaseModel):
    total: int
    prospects: list[ProspectResponse]


@router.get("/", response_model=ProspectListResponse)
async def list_prospects(
    status: ProspectStatus | None = None,
    platform: Platform | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List all discovered prospects with optional filters."""
    query = select(Prospect).offset(offset).limit(limit).order_by(Prospect.discovered_at.desc())

    if status:
        query = query.where(Prospect.status == status)
    if platform:
        query = query.where(Prospect.primary_platform == platform)

    result = await db.execute(query)
    prospects = result.scalars().all()

    count_query = select(Prospect)
    if status:
        count_query = count_query.where(Prospect.status == status)
    if platform:
        count_query = count_query.where(Prospect.primary_platform == platform)
    count_result = await db.execute(count_query)
    total = len(count_result.scalars().all())

    return ProspectListResponse(
        total=total,
        prospects=[ProspectResponse.model_validate(p) for p in prospects],
    )


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(prospect_id: int, db: AsyncSession = Depends(get_db)):
    """Get a single prospect by ID."""
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return ProspectResponse.model_validate(prospect)
