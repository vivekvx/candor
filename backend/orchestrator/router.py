from enum import Enum
from typing import Optional


class AgentRole(str, Enum):
    ADVOCATE = "advocate"
    CHALLENGER = "challenger"
    ARBITRATOR = "arbitrator"


class ModelTier(str, Enum):
    FAST = "fast"
    QUALITY = "quality"


MODEL_CONFIG = {
    ModelTier.FAST: "groq/llama-3.3-70b-versatile",
    ModelTier.QUALITY: "groq/llama-3.3-70b-versatile",
}

ROLE_TIERS = {
    AgentRole.ADVOCATE: ModelTier.FAST,
    AgentRole.CHALLENGER: ModelTier.QUALITY,
    AgentRole.ARBITRATOR: ModelTier.QUALITY,
}


def get_model_for_role(role: AgentRole, override_model: Optional[str] = None) -> str:
    if override_model:
        return override_model
    tier = ROLE_TIERS[role]
    return MODEL_CONFIG[tier]


def get_available_models() -> list[dict]:
    return [
        {"id": "groq/llama-3.3-70b-versatile", "name": "Llama 3.3 70B", "provider": "Groq", "free": True, "speed": "fast"},
        {"id": "anthropic/claude-sonnet-4-5", "name": "Claude Sonnet 4.5", "provider": "Anthropic", "free": False, "speed": "medium"},
        {"id": "gemini/gemini-1.5-flash", "name": "Gemini 1.5 Flash", "provider": "Google", "free": False, "speed": "fast"},
        {"id": "mistral/mistral-large-latest", "name": "Mistral Large", "provider": "Mistral", "free": False, "speed": "medium"},
    ]
