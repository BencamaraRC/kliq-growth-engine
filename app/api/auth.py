"""JWT authentication endpoints."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import bcrypt
import jwt
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.dependencies import get_current_user_from_token
from app.config import settings

router = APIRouter()

# Load auth config
_auth_config_path = Path(__file__).parent.parent.parent / "dashboard" / "auth_config.yaml"
with open(_auth_config_path) as f:
    _auth_cfg = yaml.safe_load(f)
_users = _auth_cfg["credentials"]["usernames"]

JWT_SECRET = settings.claim_secret_key
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_DAYS = 7


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserResponse(BaseModel):
    username: str
    name: str


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest):
    """Authenticate with username/password, return JWT."""
    user = _users.get(body.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    stored_hash = user["password"].encode("utf-8")
    if not bcrypt.checkpw(body.password.encode("utf-8"), stored_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    payload = {
        "sub": body.username,
        "name": user["name"],
        "exp": datetime.now(timezone.utc) + timedelta(days=JWT_EXPIRY_DAYS),
        "iat": datetime.now(timezone.utc),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return LoginResponse(
        access_token=token,
        user={"username": body.username, "name": user["name"]},
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = get_current_user_from_token):
    """Return current authenticated user."""
    return UserResponse(username=current_user["sub"], name=current_user["name"])
