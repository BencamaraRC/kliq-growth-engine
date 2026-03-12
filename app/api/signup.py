"""User registration endpoint."""

from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import User
from app.db.session import get_db

router = APIRouter()

JWT_SECRET = settings.claim_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class SignupResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


@router.post("/signup", response_model=SignupResponse)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user account."""
    # Check if email already exists
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    if len(body.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    # Hash password
    password_hash = bcrypt.hashpw(
        body.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    # Create user
    user = User(
        email=body.email,
        password_hash=password_hash,
        name=body.name,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate JWT
    payload = {
        "sub": body.email,
        "name": body.name,
        "user_id": user.id,
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return SignupResponse(
        access_token=token,
        user={"username": body.email, "name": body.name},
    )
