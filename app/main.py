from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import campaigns, linkedin, onboarding, pipeline, prospects, webhooks
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

app.include_router(health_router)
app.include_router(scheduler_router)
app.include_router(prospects.router, prefix="/api/prospects", tags=["prospects"])
app.include_router(campaigns.router, prefix="/api/campaigns", tags=["campaigns"])
app.include_router(pipeline.router, prefix="/api/pipeline", tags=["pipeline"])
app.include_router(webhooks.router, prefix="/api/webhooks", tags=["webhooks"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(linkedin.router, prefix="/api/linkedin", tags=["linkedin"])
app.include_router(preview_router.router, tags=["preview"])
app.include_router(claim_router.router, tags=["claim"])
