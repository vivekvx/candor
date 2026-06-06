import os

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


@app.on_event("startup")
async def startup_event():
    """
    Set provider API keys as environment variables on server startup.

    LiteLLM reads these environment variables when making calls to each
    provider. Keys are only set when non-empty so missing keys do not
    overwrite any system-level values with empty strings.
    """
    if settings.groq_api_key:
        os.environ["GROQ_API_KEY"] = settings.groq_api_key
    if settings.gemini_api_key:
        os.environ["GEMINI_API_KEY"] = settings.gemini_api_key
    if settings.anthropic_api_key:
        os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
