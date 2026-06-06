from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.routes.debate import router as debate_router
from backend.api.routes.health import router as health_router
from backend.config import settings

app = FastAPI(title="Candor API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(debate_router)
app.include_router(health_router)
