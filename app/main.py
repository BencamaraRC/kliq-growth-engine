from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import campaigns, onboarding, pipeline, prospects, webhooks
from app.claim import router as claim_router
from app.preview import router as preview_router
from app.config import settings
from app.db.session import engine


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

app.include_router(prospects.router, prefix="/api/prospects", tags=["prospects"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(preview_router.router, tags=["preview"])
app.include_router(claim_router.router, tags=["claim"])


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.app_env}
