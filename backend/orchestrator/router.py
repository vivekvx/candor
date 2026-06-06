from enum import Enum
from typing import Optional

from backend.config import settings


class AgentRole(str, Enum):
    ADVOCATE = "advocate"
    CHALLENGER = "challenger"
    ARBITRATOR = "arbitrator"


class ModelTier(str, Enum):
    FAST = "fast"
    QUALITY = "quality"


def get_fast_model() -> str:
    return "groq/llama-3.3-70b-versatile"


def get_quality_model() -> str:
    if settings.anthropic_api_key:
        return "anthropic/claude-haiku-3-5"
    return "groq/llama-3.3-70b-versatile"


ROLE_TIER_MAP = {
    "advocate_round1": ModelTier.FAST,
    "challenger_round1": ModelTier.FAST,
    "advocate_round2": ModelTier.FAST,
    "challenger_round2": ModelTier.QUALITY,
    "arbitrator": ModelTier.QUALITY,
}


def get_model_for_step(step: str, override_model: Optional[str] = None) -> str:
    if override_model and override_model != "groq/llama-3.3-70b-versatile":
        return override_model
    tier = ROLE_TIER_MAP.get(step, ModelTier.FAST)
    if tier == ModelTier.QUALITY:
        return get_quality_model()
    return get_fast_model()


def get_available_models() -> list[dict]:
    return [
        {
            "id": "groq/llama-3.3-70b-versatile",
            "name": "Llama 3.3 70B",
            "provider": "Groq",
            "free": True,
            "speed": "fast",
            "note": "Default — free and fast",
        },
        {
            "id": "anthropic/claude-haiku-3-5",
            "name": "Claude Haiku 3.5",
            "provider": "Anthropic",
            "free": False,
            "speed": "fast",
            "note": "Fast Claude model",
        },
        {
            "id": "anthropic/claude-sonnet-4-5",
            "name": "Claude Sonnet 4.5",
            "provider": "Anthropic",
            "free": False,
            "speed": "medium",
            "note": "Best quality",
        },
        {
            "id": "gemini/gemini-1.5-flash",
            "name": "Gemini 1.5 Flash",
            "provider": "Google",
            "free": False,
            "speed": "fast",
            "note": "Google's fast model",
        },
    ]
