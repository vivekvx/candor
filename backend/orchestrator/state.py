# Debate state dataclass — shared across all agents
from dataclasses import dataclass, field


@dataclass
class DebateState:
    query: str
    model: str = "groq/llama-3.3-70b-versatile"
    advocate_research: str = ""
    challenger_research: str = ""
    advocate_rebuttal: str = ""
    challenger_rebuttal: str = ""
    verdict: dict = field(default_factory=dict)
    round: int = 0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
