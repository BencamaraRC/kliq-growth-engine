"""Shared FastAPI dependencies."""

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

import jwt

from app.config import settings

JWT_SECRET = settings.claim_secret_key
JWT_ALGORITHM = "HS256"

_bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> dict:
    """Decode JWT from Authorization header and return user payload."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Convenience alias for use as a Depends() in route signatures
get_current_user_from_token = Depends(get_current_user)
