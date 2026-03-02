"""Health check endpoints for liveness and readiness probes."""

import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db.session import async_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Liveness probe — always returns 200 if the process is running."""
    return {"status": "ok", "env": settings.app_env}


@router.get("/health/ready")
async def readiness():
    """Readiness probe — checks database and Redis connectivity."""
    checks = {}

    # Check PostgreSQL
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = all(v == "ok" for v in checks.values())
    status_code = 200 if all_ok else 503

    from fastapi.responses import JSONResponse

    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if all_ok else "degraded", "checks": checks},
    )
