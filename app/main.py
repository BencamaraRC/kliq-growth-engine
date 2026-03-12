import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import (
    analytics,
    auth,
    blogs,
    campaigns,
    linkedin,
    onboarding,
    pipeline,
    prospects,
    signup,
    webhooks,
)
from app.api.health import router as health_router
from app.api.scheduler import router as scheduler_router
from app.claim import router as claim_router
from app.db.session import engine
from app.preview import router as preview_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="KLIQ Growth Engine",
    description="Automated coach discovery, webstore generation, and outreach",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Routes ---
app.include_router(health_router)
app.include_router(scheduler_router)
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(signup.router, prefix="/api/auth", tags=["auth"])
app.include_router(blogs.router, prefix="/api/blogs", tags=["blogs"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(prospects.router, prefix="/api/prospects", tags=["prospects"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(linkedin.router, prefix="/api/linkedin", tags=["linkedin"])
app.include_router(preview_router.router, tags=["preview"])
app.include_router(claim_router.router, tags=["claim"])

# --- Static File Serving (React SPA) ---
_frontend_dist = Path(__file__).parent.parent / "frontend" / "dist"

if _frontend_dist.exists():
    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        """Serve React SPA for all non-API routes."""
        file_path = _frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))
