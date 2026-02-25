"""Campaign API routes — manage outreach campaigns."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Campaign, CampaignStatus
from app.db.session import get_db

router = APIRouter()


class CampaignCreate(BaseModel):
    name: str
    platform_filter: str | None = None
    niche_filter: list[str] | None = None
    min_followers: int = 0


class CampaignResponse(BaseModel):
    id: int
    name: str
    status: str
    platform_filter: str | None
    niche_filter: list | None
    min_followers: int

    model_config = {"from_attributes": True}


@router.get("/", response_model=list[CampaignResponse])
async def list_campaigns(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).order_by(Campaign.created_at.desc()))
    return [CampaignResponse.model_validate(c) for c in result.scalars().all()]


@router.post("/", response_model=CampaignResponse)
async def create_campaign(data: CampaignCreate, db: AsyncSession = Depends(get_db)):
    campaign = Campaign(
        name=data.name,
        platform_filter=data.platform_filter,
        niche_filter=data.niche_filter,
        min_followers=data.min_followers,
        status=CampaignStatus.DRAFT,
    )
    db.add(campaign)
    await db.commit()
    await db.refresh(campaign)
    return CampaignResponse.model_validate(campaign)


@router.post("/{campaign_id}/activate", response_model=CampaignResponse)
async def activate_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.ACTIVE
    await db.commit()
    await db.refresh(campaign)
    return CampaignResponse.model_validate(campaign)


@router.post("/{campaign_id}/pause", response_model=CampaignResponse)
async def pause_campaign(campaign_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign.status = CampaignStatus.PAUSED
    await db.commit()
    await db.refresh(campaign)
    return CampaignResponse.model_validate(campaign)
