"""Prospect API routes — CRUD, detail, filters, and operations."""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import String, select, text, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.models import Platform, Prospect, ProspectStatus
from app.db.session import get_db

router = APIRouter()


# --- Response Models ---


class ProspectResponse(BaseModel):
    id: int
    name: str
    email: str | None
    status: str
    primary_platform: str
    primary_platform_id: str
    profile_image_url: str | None = None
    website_url: str | None = None
    social_links: dict | None = None
    primary_platform_url: str | None = None
    follower_count: int
    subscriber_count: int
    niche_tags: list | None
    kliq_application_id: int | None
    kliq_store_url: str | None
    discovered_at: datetime | None = None
    claimed_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProspectListResponse(BaseModel):
    total: int
    prospects: list[ProspectResponse]


class ProspectDetailResponse(BaseModel):
    """Full prospect detail with all related data."""
    id: int
    name: str
    email: str | None
    first_name: str | None
    last_name: str | None
    status: str
    primary_platform: str
    primary_platform_id: str
    primary_platform_url: str | None
    bio: str | None
    profile_image_url: str | None
    banner_image_url: str | None
    website_url: str | None
    social_links: dict | None
    linkedin_url: str | None
    linkedin_found: bool
    niche_tags: list | None
    location: str | None
    follower_count: int
    subscriber_count: int
    content_count: int
    brand_colors: list | None
    kliq_application_id: int | None
    kliq_store_url: str | None
    claim_token: str | None
    discovered_at: str | None
    store_created_at: str | None
    claimed_at: str | None
    created_at: str | None
    updated_at: str | None
    platform_profiles: list[dict]
    scraped_content: list[dict]
    generated_content: list[dict]
    campaign_events: list[dict]
    scraped_pricing: list[dict]


class OperationsProspect(BaseModel):
    id: int
    name: str
    email: str | None
    status: str
    platform: str
    followers: int
    claim_token: str | None
    store_url: str | None
    discovered: str | None


# --- Existing Endpoints ---


@router.get("/", response_model=ProspectListResponse)
async def list_prospects(
    status: ProspectStatus | None = None,
    platform: Platform | None = None,
    niche: str | None = None,
    search: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """List all discovered prospects with optional filters."""
    query = select(Prospect).offset(offset).limit(limit).order_by(Prospect.discovered_at.desc())

    if status:
        query = query.where(Prospect.status == status)
    if platform:
        query = query.where(Prospect.primary_platform == platform)
    if niche:
        query = query.where(Prospect.niche_tags.cast(String).ilike(f"%{niche}%"))
    if search:
        query = query.where(
            (Prospect.name.ilike(f"%{search}%")) | (Prospect.email.ilike(f"%{search}%"))
        )

    result = await db.execute(query)
    prospects = result.scalars().all()

    # Count query
    count_query = select(func.count(Prospect.id))
    if status:
        count_query = count_query.where(Prospect.status == status)
    if platform:
        count_query = count_query.where(Prospect.primary_platform == platform)
    if niche:
        count_query = count_query.where(Prospect.niche_tags.cast(String).ilike(f"%{niche}%"))
    if search:
        count_query = count_query.where(
            (Prospect.name.ilike(f"%{search}%")) | (Prospect.email.ilike(f"%{search}%"))
        )
    total = (await db.execute(count_query)).scalar() or 0

    return ProspectListResponse(
        total=total,
        prospects=[ProspectResponse.model_validate(p) for p in prospects],
    )


class ProspectUpdate(BaseModel):
    profile_image_url: str | None = None
    banner_image_url: str | None = None


@router.patch("/{prospect_id}", response_model=ProspectResponse)
async def update_prospect(
    prospect_id: int,
    body: ProspectUpdate,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Update specific fields on a prospect."""
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(prospect, field, value)

    await db.commit()
    await db.refresh(prospect)
    return ProspectResponse.model_validate(prospect)


@router.get("/{prospect_id}", response_model=ProspectResponse)
async def get_prospect(
    prospect_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single prospect by ID."""
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    return ProspectResponse.model_validate(prospect)


class SignupDetailsResponse(BaseModel):
    id: int
    name: str
    email: str | None
    coach_type: str
    profile_image: str | None
    banner_image: str | None


@router.get("/{prospect_id}/signup", response_model=SignupDetailsResponse)
async def get_signup_details(prospect_id: int, db: AsyncSession = Depends(get_db)):
    """Get prospect details for the CMS signup page.

    Called by the CMS when a coach is redirected to the signup page
    with ?id={prospect_id}. Returns pre-filled details for account creation.
    """
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    coach_type = ""
    if prospect.niche_tags and isinstance(prospect.niche_tags, list) and prospect.niche_tags:
        coach_type = prospect.niche_tags[0]
    elif prospect.primary_platform:
        coach_type = prospect.primary_platform.value.lower() + " coach"

    return SignupDetailsResponse(
        id=prospect.id,
        name=prospect.name,
        email=prospect.email,
        coach_type=coach_type,
        profile_image=prospect.profile_image_url,
        banner_image=prospect.banner_image_url,
    )


# --- New Endpoints ---


@router.get("/{prospect_id}/detail", response_model=ProspectDetailResponse)
async def get_prospect_detail(
    prospect_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Full prospect detail with scraped content, generated content, events, pricing."""
    row = (
        await db.execute(
            text("SELECT * FROM prospects WHERE id = :id"), {"id": prospect_id}
        )
    ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Prospect not found")

    prospect = dict(row._mapping)

    # Related data
    profiles = (
        await db.execute(
            text("SELECT * FROM platform_profiles WHERE prospect_id = :id"), {"id": prospect_id}
        )
    ).fetchall()

    content = (
        await db.execute(
            text(
                "SELECT * FROM scraped_content WHERE prospect_id = :id ORDER BY view_count DESC"
            ),
            {"id": prospect_id},
        )
    ).fetchall()

    generated = (
        await db.execute(
            text("SELECT * FROM generated_content WHERE prospect_id = :id"), {"id": prospect_id}
        )
    ).fetchall()

    events = (
        await db.execute(
            text("SELECT * FROM campaign_events WHERE prospect_id = :id ORDER BY sent_at"),
            {"id": prospect_id},
        )
    ).fetchall()

    pricing = (
        await db.execute(
            text(
                "SELECT * FROM scraped_pricing WHERE prospect_id = :id ORDER BY price_amount"
            ),
            {"id": prospect_id},
        )
    ).fetchall()

    def _serialize_rows(rows):
        result = []
        for r in rows:
            d = dict(r._mapping)
            # Convert datetime/enum values to strings
            for k, v in d.items():
                if hasattr(v, "isoformat"):
                    d[k] = v.isoformat()
                elif hasattr(v, "value"):
                    d[k] = v.value
            result.append(d)
        return result

    # Serialize prospect datetimes
    for k, v in prospect.items():
        if hasattr(v, "isoformat"):
            prospect[k] = v.isoformat()
        elif hasattr(v, "value"):
            prospect[k] = v.value

    prospect["platform_profiles"] = _serialize_rows(profiles)
    prospect["scraped_content"] = _serialize_rows(content)
    prospect["generated_content"] = _serialize_rows(generated)
    prospect["campaign_events"] = _serialize_rows(events)
    prospect["scraped_pricing"] = _serialize_rows(pricing)

    return ProspectDetailResponse(**prospect)


@router.get("/filters/platforms")
async def get_filter_platforms(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Distinct platform values for filter dropdowns."""
    result = (
        await db.execute(
            text(
                "SELECT DISTINCT primary_platform FROM prospects "
                "WHERE primary_platform IS NOT NULL ORDER BY primary_platform"
            )
        )
    ).fetchall()
    return [row[0] for row in result]


@router.get("/filters/niches")
async def get_filter_niches(
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Distinct niche tags for filter dropdowns."""
    result = (
        await db.execute(
            text("""
                SELECT DISTINCT tag
                FROM prospects, jsonb_array_elements_text(niche_tags::jsonb) AS tag
                WHERE niche_tags IS NOT NULL
                ORDER BY tag
            """)
        )
    ).fetchall()
    return [row[0] for row in result]


@router.patch("/{prospect_id}/reject")
async def reject_prospect(
    prospect_id: int,
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Set prospect status to REJECTED."""
    result = await db.execute(select(Prospect).where(Prospect.id == prospect_id))
    prospect = result.scalar_one_or_none()
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")

    prospect.status = ProspectStatus.REJECTED
    await db.commit()
    return {"ok": True, "id": prospect_id, "status": "REJECTED"}


@router.get("/operations/list", response_model=list[OperationsProspect])
async def list_operations_prospects(
    status: str | None = None,
    platform: str | None = None,
    search: str | None = None,
    limit: int = Query(default=100, le=500),
    db: AsyncSession = Depends(get_db),
    _user: dict = Depends(get_current_user),
):
    """Prospects list for operations page, includes claim_token for preview URLs."""
    conditions = []
    params: dict = {"limit": limit}

    if status:
        conditions.append("status = :status")
        params["status"] = status
    if platform:
        conditions.append("primary_platform = :platform")
        params["platform"] = platform
    if search:
        conditions.append("(name ILIKE :search OR email ILIKE :search)")
        params["search"] = f"%{search}%"

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    result = (
        await db.execute(
            text(f"""
                SELECT id, name, email, status, primary_platform,
                       follower_count, claim_token, kliq_store_url, discovered_at
                FROM prospects
                {where}
                ORDER BY discovered_at DESC
                LIMIT :limit
            """),
            params,
        )
    ).fetchall()

    return [
        OperationsProspect(
            id=row[0],
            name=row[1],
            email=row[2],
            status=row[3],
            platform=row[4],
            followers=row[5],
            claim_token=row[6],
            store_url=row[7],
            discovered=str(row[8]) if row[8] else None,
        )
        for row in result
    ]
