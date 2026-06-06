import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DebateState:
    query: str
    model: str = "groq/llama-3.3-70b-versatile"

    advocate_research: str = ""
    challenger_research: str = ""

    advocate_rebuttal: str = ""
    challenger_rebuttal: str = ""

    verdict: dict = field(default_factory=dict)
    step_costs: dict = field(default_factory=dict)

    round: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    started_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None

    def add_usage(self, input_tokens: int, output_tokens: int, cost: float):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += cost
