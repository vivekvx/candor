import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.debate import router as debate_router
from api.routes.health import router as health_router
from config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="Candor API", version="0.1.0")

allowed_origins = [
    os.getenv("FRONTEND_URL", settings.frontend_url),
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(debate_router)
app.include_router(health_router)


@app.get("/ping")
async def ping():
    """Health check endpoint for Railway keep-warm."""
    return {"status": "ok"}


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
    if settings.openrouter_api_key:
        os.environ["OPENROUTER_API_KEY"] = settings.openrouter_api_key

    # Wire Langfuse observability into every LiteLLM call
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        import litellm
        litellm.success_callback = ["langfuse"]
        litellm.failure_callback = ["langfuse"]
        logger.info("Langfuse observability enabled")
