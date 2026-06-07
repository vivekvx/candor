from enum import Enum
from typing import Optional

from config import settings


class AgentRole(str, Enum):
    ADVOCATE = "advocate"
    CHALLENGER = "challenger"
    ARBITRATOR = "arbitrator"


class ModelTier(str, Enum):
    FAST = "fast"
    QUALITY = "quality"


# All supported models — shown only when their provider key is configured
ALL_MODELS = [
    {
        "id": "groq/llama-3.3-70b-versatile",
        "name": "Llama 3.3 70B",
        "provider": "Groq",
        "key_field": "groq_api_key",
        "free": True,
        "speed": "fast",
        "note": "Default — free and fast",
    },
    {
        "id": "groq/llama-3.1-8b-instant",
        "name": "Llama 3.1 8B Instant",
        "provider": "Groq",
        "key_field": "groq_api_key",
        "free": True,
        "speed": "fast",
        "note": "Fastest Groq model",
    },
    {
        "id": "anthropic/claude-haiku-3-5",
        "name": "Claude Haiku 3.5",
        "provider": "Anthropic",
        "key_field": "anthropic_api_key",
        "free": False,
        "speed": "fast",
        "note": "Fast Claude model",
    },
    {
        "id": "anthropic/claude-sonnet-4-5",
        "name": "Claude Sonnet 4.5",
        "provider": "Anthropic",
        "key_field": "anthropic_api_key",
        "free": False,
        "speed": "medium",
        "note": "Best quality",
    },
    {
        "id": "gemini/gemini-1.5-flash",
        "name": "Gemini 1.5 Flash",
        "provider": "Google",
        "key_field": "gemini_api_key",
        "free": False,
        "speed": "fast",
        "note": "Google's fast model",
    },
    {
        "id": "gemini/gemini-2.0-flash",
        "name": "Gemini 2.0 Flash",
        "provider": "Google",
        "key_field": "gemini_api_key",
        "free": False,
        "speed": "fast",
        "note": "Latest Gemini Flash",
    },
    {
        "id": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
        "name": "Llama 3.3 70B (OpenRouter)",
        "provider": "OpenRouter",
        "key_field": "openrouter_api_key",
        "free": True,
        "speed": "fast",
        "note": "Free via OpenRouter — separate token pool from Groq",
    },
    {
        "id": "openrouter/qwen/qwen3-14b:free",
        "name": "Qwen3 14B (OpenRouter)",
        "provider": "OpenRouter",
        "key_field": "openrouter_api_key",
        "free": True,
        "speed": "medium",
        "note": "Free reasoning model via OpenRouter",
    },
]


def _has_key(key_field: str) -> bool:
    value = getattr(settings, key_field, None)
    return bool(value and len(value) > 8)


def get_available_models() -> list[dict]:
    """Return only models whose provider API key is configured."""
    available = [m for m in ALL_MODELS if _has_key(m["key_field"])]
    # Always ensure at least one model appears (Groq Llama as fallback)
    if not available:
        available = [ALL_MODELS[0]]
    return [
        {k: v for k, v in m.items() if k != "key_field"}
        for m in available
    ]


def get_fast_model() -> str:
    if _has_key("groq_api_key"):
        return "groq/llama-3.3-70b-versatile"
    if _has_key("gemini_api_key"):
        return "gemini/gemini-1.5-flash"
    if _has_key("anthropic_api_key"):
        return "anthropic/claude-haiku-3-5"
    return "groq/llama-3.3-70b-versatile"


def get_quality_model() -> str:
    if _has_key("anthropic_api_key"):
        return "anthropic/claude-haiku-3-5"
    if _has_key("gemini_api_key"):
        return "gemini/gemini-2.0-flash"
    if _has_key("groq_api_key"):
        return "groq/llama-3.3-70b-versatile"
    return "groq/llama-3.3-70b-versatile"


def get_fallback_models(failed_model: str) -> list[str]:
    """
    Return ordered list of fallback models to try when `failed_model` fails.
    Excludes the failed model and prefers different providers.
    """
    candidates = []
    # Different provider first
    # NOTE: anthropic deliberately excluded here — _has_key only checks the
    # key is *set*, not that the account carries credits. A configured-but-
    # uncredited Anthropic key produces a misleading "credit balance too low"
    # as the terminal fallback error, masking the real rate-limit cause.
    if not failed_model.startswith("groq/") and _has_key("groq_api_key"):
        candidates.append("groq/llama-3.3-70b-versatile")
    if not failed_model.startswith("gemini/") and _has_key("gemini_api_key"):
        candidates.append("gemini/gemini-2.0-flash")
    # Same provider, different model
    if failed_model == "groq/llama-3.3-70b-versatile" and _has_key("groq_api_key"):
        candidates.append("groq/llama-3.1-8b-instant")
    return candidates


ROLE_TIER_MAP = {
    "advocate_round1": ModelTier.FAST,
    "challenger_round1": ModelTier.FAST,
    "advocate_round2": ModelTier.FAST,
    "challenger_round2": ModelTier.QUALITY,
    "arbitrator": ModelTier.FAST,
}


# Spreads token usage across two providers simultaneously: Advocate draws
# from Groq's pool, Challenger draws from OpenRouter's separate pool.
# Both run comparable Llama 3.3 70B models, so quality stays consistent
# while effective free-tier capacity roughly doubles.
LOAD_BALANCED_STEP_MODELS = {
    "advocate_round1": "groq/llama-3.3-70b-versatile",
    "challenger_round1": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    "advocate_round2": "groq/llama-3.3-70b-versatile",
    "challenger_round2": "openrouter/qwen/qwen3-14b:free",
    "arbitrator": "groq/llama-3.3-70b-versatile",
}


def get_load_balanced_model(step: str, override_model: Optional[str] = None) -> str:
    """
    Return a load-balanced model assignment for a debate step.

    Spreads token usage across Groq and OpenRouter so the two providers'
    rate-limit pools are consumed in parallel rather than serially.
    If the user explicitly selected a non-default model, that choice is
    honored for every step instead.
    """
    if override_model and override_model != "groq/llama-3.3-70b-versatile":
        return override_model
    return LOAD_BALANCED_STEP_MODELS.get(step, "groq/llama-3.3-70b-versatile")


def get_model_for_step(step: str, override_model: Optional[str] = None) -> str:
    if override_model and override_model != "groq/llama-3.3-70b-versatile":
        return override_model
    tier = ROLE_TIER_MAP.get(step, ModelTier.FAST)
    if tier == ModelTier.QUALITY:
        return get_quality_model()
    return get_fast_model()
