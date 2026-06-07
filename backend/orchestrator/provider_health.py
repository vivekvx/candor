"""
Provider health tracker for Candor debate system.

Tracks which providers have recently failed due to rate limits.
Skips recently-failed providers to reduce wasted API calls and
improve debate completion rate.

This makes the fallback chain proactive — it avoids known-bad
providers instead of discovering they're exhausted mid-debate.
"""

import time
import logging

logger = logging.getLogger(__name__)

# How long to consider a provider unhealthy after a rate limit error
UNHEALTHY_DURATION_SECONDS = 60

# Tracks last rate limit error time per provider
# Key: provider prefix (e.g. "groq", "openrouter", "gemini")
_provider_last_error: dict[str, float] = {}


def mark_provider_rate_limited(model_string: str) -> None:
    """
    Mark a provider as rate limited.

    Called when a rate limit error is detected for a model. Records
    the current time so is_provider_healthy can skip this provider
    for UNHEALTHY_DURATION_SECONDS.
    """
    provider = extract_provider_prefix(model_string)
    _provider_last_error[provider] = time.time()
    logger.warning(
        "Provider '%s' marked as rate limited. Will skip for %d seconds.",
        provider, UNHEALTHY_DURATION_SECONDS,
    )


def is_provider_healthy(model_string: str) -> bool:
    """
    Check if a provider is currently healthy (not recently rate limited).

    Returns True if the provider has no recorded rate-limit error, or
    if enough time has passed since its last recorded error.
    """
    provider = extract_provider_prefix(model_string)
    last_error_time = _provider_last_error.get(provider)

    if last_error_time is None:
        return True

    seconds_since_error = time.time() - last_error_time
    return seconds_since_error >= UNHEALTHY_DURATION_SECONDS


def get_healthy_fallback_chain(
    preferred_model: str,
    full_chain: list[str],
) -> list[str]:
    """
    Build a fallback priority list with unhealthy providers deprioritized.

    Always keeps every model reachable — even unhealthy ones — but puts
    the preferred model first, then healthy fallbacks, then unhealthy
    fallbacks as a last resort. This way a debate never fails outright
    just because every provider looked unhealthy a minute ago.
    """
    healthy_models = [
        model for model in full_chain
        if is_provider_healthy(model)
    ]
    unhealthy_models = [
        model for model in full_chain
        if not is_provider_healthy(model)
    ]

    all_models = []
    if preferred_model not in all_models:
        all_models.append(preferred_model)
    for model in healthy_models:
        if model not in all_models:
            all_models.append(model)
    for model in unhealthy_models:
        if model not in all_models:
            all_models.append(model)

    return all_models


def extract_provider_prefix(model_string: str) -> str:
    """
    Extract the provider name from a LiteLLM model string.

    e.g. "groq/llama-3.3-70b" -> "groq"
         "openrouter/deepseek/deepseek-r1:free" -> "openrouter"
    """
    if "/" in model_string:
        return model_string.split("/")[0]
    return model_string
