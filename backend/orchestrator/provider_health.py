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

# Models confirmed permanently dead this session (e.g. 404 Not Found —
# the endpoint doesn't exist, so retrying after a cooldown won't help).
# Key: full LiteLLM model string (e.g. "openrouter/deepseek/deepseek-r1:free")
_permanently_dead_models: set[str] = set()


def mark_dead_permanent(model_string: str) -> None:
    """
    Permanently exclude a model from the fallback chain for this process.

    Called on litellm.NotFoundError (HTTP 404) — unlike a rate limit, a
    missing endpoint will not recover after a cooldown window, so we stop
    wasting calls on it for the rest of the session.
    """
    _permanently_dead_models.add(model_string)
    logger.warning(
        "Model '%s' returned 404 Not Found — permanently marked dead for this session.",
        model_string,
    )


def is_model_dead(model_string: str) -> bool:
    """Return True if this exact model string was permanently marked dead."""
    return model_string in _permanently_dead_models


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


def seconds_until_chain_recovers(model_chain: list[str]) -> int:
    """
    Estimate how long until the soonest provider in this chain becomes
    healthy again — i.e. how long a user should wait before retrying.

    Used to turn a flat "all providers exhausted" failure into a useful
    "high demand, try again in ~N minutes" message. Permanently dead
    models are ignored (no cooldown will revive them); models with no
    recorded rate-limit error contribute 0 (they're healthy right now —
    if the chain still failed, the real cause is something else, e.g.
    every live model being simultaneously rate limited mid-request).

    Returns 0 if no live model in the chain has a recorded rate-limit time.
    """
    live_models = [m for m in model_chain if not is_model_dead(m)]
    if not live_models:
        return 0

    waits = []
    for model in live_models:
        provider = extract_provider_prefix(model)
        last_error_time = _provider_last_error.get(provider)
        if last_error_time is None:
            continue
        remaining = UNHEALTHY_DURATION_SECONDS - (time.time() - last_error_time)
        waits.append(max(0, remaining))

    if not waits:
        return 0
    return int(min(waits))


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
    live_chain = [model for model in full_chain if not is_model_dead(model)]

    healthy_models = [
        model for model in live_chain
        if is_provider_healthy(model)
    ]
    unhealthy_models = [
        model for model in live_chain
        if not is_provider_healthy(model)
    ]

    all_models = []
    if not is_model_dead(preferred_model) and preferred_model not in all_models:
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
         "groq/llama-3.3-70b:paid" -> "groq"
         "openrouter/deepseek/deepseek-r1:free" -> "openrouter"
    """
    # Strip :paid/:free suffix if present
    clean = model_string.split(":")[0]
    if "/" in clean:
        return clean.split("/")[0]
    return clean
