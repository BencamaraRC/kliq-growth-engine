"""Onboarding progress API — tracks post-claim activation steps."""

import logging

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.claim.queries import complete_onboarding_step, get_onboarding_dict
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


class StepCompleteRequest(BaseModel):
    step: str


@router.get("/{prospect_id}")
async def get_onboarding(
    prospect_id: int,
    session: AsyncSession = Depends(get_db),
):
    """Fetch onboarding progress for a prospect."""
    return await get_onboarding_dict(session, prospect_id)


@router.post("/{prospect_id}/complete-step")
async def mark_step_complete(
    prospect_id: int,
    body: StepCompleteRequest,
    session: AsyncSession = Depends(get_db),
):
    """Mark an onboarding step as complete."""
    try:
        result = await complete_onboarding_step(session, prospect_id, body.step)
        return result
    except ValueError as e:
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail=str(e))
